import calendar
import csv
import datetime
import glob
import io
import json
import os
import zipfile
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from ssm_parameter_store import SSMParameterStore
from webdriver_wrapper import WebDriverWrapper

store_map = {
    '20025': '8d6b329b-4976-4ef7-8411-3a416614a726',
    '20358': 'ee0492bb-edd6-507a-83eb-1d1427e3ff7d',
}


class UberEats:
    """"""

    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix="/prod")["ubereats"]
        self._month_abbr_to_num = {
            name: num for num, name in enumerate(calendar.month_abbr) if num
        }
        self._month_to_num = {
            name: num for num, name in enumerate(calendar.month_name) if num
        }
        self._day_endings = {
            1: "st",
            2: "nd",
            3: "rd",
            21: "st",
            22: "nd",
            23: "rd",
            31: "st",
        }
        self._driver = None

    """
    """

    def _login(self):
        self._driver = WebDriverWrapper(download_location="/tmp")
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get("https://restaurant.uber.com/manager/logout")
        sleep(5)
        driver.get("https://restaurant.uber.com/")
        driver.find_element_by_id("useridInput").send_keys(
            self._parameters["user"] + Keys.RETURN
        )
        driver.find_element_by_id("password").send_keys(
            self._parameters["password"] + Keys.RETURN
        )
        sleep(12)
        # for element, pin in zip(
        #     driver.find_elements_by_xpath("//input"), self._parameters["pin"]
        # ):
        #     element.send_keys(pin)
        # driver.find_element_by_xpath("//button").click()
        # sleep(10)
        return

    def __get_month_year(self):
        driver = self._driver._driver
        month_ele = driver.find_element_by_xpath('//button[@aria-label="Previous month."]'
                                             ).find_element_by_xpath("following-sibling::*")
        month = month_ele.text.split(' ')[0]
        month_ele = month_ele.find_element_by_xpath("following-sibling::*")
        year = month_ele.text.split(' ')[0]
        month = self._month_to_num[month]
        year = int(year)
        return month, year

    def _click_date(self, qdate):
        driver = self._driver._driver
        qstr = qdate.strftime(
            "Choose %A, %B %-d{} %Y. It's available.".format(
                self._day_endings.get(qdate.day, "th")
            )
        )
        qstr2 = qdate.strftime(
            "Selected start date. %A, %B %-d{} %Y. It's available.".format(
                self._day_endings.get(qdate.day, "th")
            )
        )

        sleep(2)

        driver.find_element_by_xpath('//button[@aria-label="datepicker-input"]').click()

        sleep(3)
        year = self.__get_month_year()[1]
        while year != qdate.year:
            if year > qdate.year:
                print("moving back a month - year search")
                driver.find_element_by_xpath(
                    '//button[@aria-label="Previous month."]'
                ).click()
            elif year < qdate.year:
                print("moving forward a month - year search")
                driver.find_element_by_xpath(
                     '//button[@aria-label="Next month."]'
                ).click()
            else:
                break
            year = self.__get_month_year()[1]
        month = self.__get_month_year()[0]
        try:
            while month != qdate.month:
                if month > qdate.month:
                    print("going back a month - month search")
                    driver.find_element_by_xpath(
                        '//button[@aria-label="Previous month."]'
                    ).click()
                else:
                    print("going forward a month - month search")
                    driver.find_element_by_xpath(
                        '//button[@aria-label="Next month."]'
                    ).click()
                month = self.__get_month_year()[0]
        except Exception:
            print("month search failed trying anyway")
            pass
        try:
            print('//div[@aria-label="{}"]'.format(qstr))
            driver.find_element_by_xpath('//div[@aria-label="{}"]'.format(qstr)).click()
        except NoSuchElementException:
            print('oops')
            print(
                '//div[@aria-label="{}"]'.format(qstr2))
            driver.find_element_by_xpath(
                '//div[@aria-label="{}"]'.format(qstr2)
            ).click()
        return

    def get_payments(self, stores, start_date, end_date):
        if isinstance(start_date, type(None)):
            start_date = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday()+14)
            )
            end_date = datetime.date.today()
        for store in stores:
            qdate = start_date
            results = []

            try:
                while qdate < end_date:
                    results.extend([self.get_payment(store, qdate)])
                    qdate = qdate + datetime.timedelta(days=7)
            finally:
                #self._driver._driver.close()
                pass
        return results

    def get_payment(self, store, qdate=None):
        if isinstance(qdate, type(None)):
            qdate = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday() + 7)
            )
        if not self._driver:
            self._login()
        driver = self._driver._driver
        driver.get(
            "https://restaurant.uber.com/v2/payments?restaurantUUID=" +
            store_map[store]
        )

        notes = ""
        lines = []

        qdate2 = qdate - datetime.timedelta(days=(qdate.weekday() + 7))

        sleep(3)
        self._click_date(qdate2)
        sleep(3)
        self._click_date(qdate)
        sleep(3)

        # earnings
        earnings = driver.find_element_by_xpath('//li[@tabindex="-1"]')
        earnings.click()
        txt = earnings.find_element_by_xpath(
            '..').text.split('\n')
        print(txt)
        invoice = {
            txt[i]: self.convert_num(
                txt[i+1]) for i in range(0, len(txt), 2)
        }
        print(invoice)

        # third party
        lines.append(["1260", 'Sales', invoice['Sales']])

        # tips
        if 'Customer contributions' in invoice:
            lines.append(["2220", 'Customer contributions', invoice['Customer contributions']])
        if 'Customer Refunds' in invoice:
            lines.append(["6260", 'Customer Refunds',
                      invoice['Customer Refunds']])
        if 'Marketing' in invoice:
            lines.append(["6101", 'Uber Marketing', invoice['Marketing']])
        lines.append(["6261", 'Uber fees', invoice['Uber fees']])
        notes += str(txt)
        print(lines)

        # pay day is always Monday
        result = [
            "Uber Eats",
            qdate - datetime.timedelta(days=(qdate.weekday() - 8)),
            notes,
            lines,
            store,
        ]
        return result


    def convert_num(self, number):
        if ")" in number:
            return "-" + number[2:-1]
        else:
            return number[1:]
