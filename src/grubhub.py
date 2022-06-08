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


class Grubhub:
    """"""

    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix="/prod")["grubhub"]

    """
    """

    def _login(self):
        self._driver = WebDriverWrapper(download_location="/tmp")
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get(
         "https://restaurant.grubhub.com/financials/deposit-history/1669366/"
        )
        sleep(3)
        driver.find_elements_by_xpath("//input")[0].send_keys(
         self._parameters["user"]
        )
        sleep(4)
        driver.find_elements_by_xpath("//input")[1].send_keys(
            self._parameters["password"] + Keys.ENTER
        )
        sleep(4)
        return

    def get_payments(self, start_date=None, end_date=None):
        if isinstance(start_date, type(None)):
            start_date = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday() + 7)
            )
        if isinstance(end_date, type(None)):
            end_date = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday() - 7)
            )
        #if datetime.date.today() - start_date >= datetime.timedelta(days=30):
        #    raise ValueError("Dates outside of 30 days is not supported.")
        try:
            self._login()
            input("pause")
            driver = self._driver._driver
            driver.get(
             "https://restaurant.grubhub.com/financials/deposit-history/3192172,1669366/"
            )
            driver.find_element_by_class_name("gfr-date-picker-input__date-button").click()
            driver.find_element_by_class_name("last-30-days").click()

            sleep(15)

            results = []

            for tr in driver.find_elements_by_class_name('fin-deposits-table-row'):
                notes = ""
                lines = []
                txdate = datetime.datetime.strptime(
                    tr.text.split()[0], "%m/%d/%y"
                ).date()
                store = tr.text.split()[4].strip(" ()")
                tr.click()
                txt = driver.find_element_by_xpath(
                    '//div[@class="fin-deposit-history-deposit-details__section fin-deposit-history-deposit-details__section--bleed"]'
                ).text.replace(')', ')\n').replace('Total','Total\n').split("\n")
                print(txt)
                print(txdate)

                for i in range(0, len(txt), 2):
                    if i == 0:
                        lines.append(["1260", txt[0], self.convert_num(txt[1])])
                    elif i == len(txt) - 2:
                        continue  # skip the deposit total
                    else:
                        lines.append(["6261", txt[i], self.convert_num(txt[i + 1])])

                refunds = driver.find_elements_by_xpath("//h5")[0]
                if refunds.text.split()[0] == "Refunds":
                    # lines.append(['6260',txt[i],self.convert_num(txt[i+1])])
                    notes += str(
                        refunds.find_element_by_xpath("following-sibling::*").text
                    )
                    # this is hard so skip it
                    pass

                if start_date <= txdate and txdate <= end_date:
                    results.append(["Grubhub", txdate, notes, lines, store])
                driver.find_element_by_xpath(
                    '//div[@class="transactions-order-details-header__info-bar__close"]'
                ).click()
            return results

        finally:
            # driver.close()
            pass

    def convert_num(self, number):
        return number.replace("$", "")
