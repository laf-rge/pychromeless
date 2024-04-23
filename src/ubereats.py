import calendar
import datetime
import os
from time import sleep

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ssm_parameter_store import SSMParameterStore
from webdriver_wrapper import WebDriverWrapper

store_map = {
    '20025': '8d6b329b-4976-4ef7-8411-3a416614a726',
    '20358': 'ee0492bb-edd6-507a-83eb-1d1427e3ff7d',
    '20395': '8fdc747c-dd18-491f-8c3a-317b1b4cab3c',
    '20400': '6f845016-13f6-41fd-8cd0-08b83157b0d8',
    '20407': 'b8399c5e-1bbc-4e6c-a897-63121cf7d37c',
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
        driver.find_element(By.ID, "PHONE_NUMBER_or_EMAIL_ADDRESS").send_keys(
            self._parameters["user"] + Keys.RETURN
        )
        sleep(3)
        #driver.find_element(By.ID, "PASSWORD").send_keys(
        #    self._parameters["password"] + Keys.RETURN
        #)
        sleep(2)
        # for element, pin in zip(
        #     driver.find_elements(By.XPATH, "//input"), self._parameters["pin"]
        # ):
        #     element.send_keys(pin)
        # driver.find_element(By.XPATH, "//button").click()
        # sleep(10)
        input("pause...")
        return

    def __get_month_year(self):
        driver = self._driver._driver
        sleep(2)
        month = driver.find_element(By.XPATH, '//button[@aria-label="Previous month."]/following-sibling::*').text
        print(month)
        year = driver.find_element(By.XPATH, '//button[@aria-label="Previous month."]/following-sibling::*/following-sibling::*').text
        month = self._month_to_num[month]
        year = int(year)
        return month, year

    def _click_date(self, qdate):
        driver = self._driver._driver
        ActionChains(driver).send_keys(Keys.RETURN).perform()
        start_date = driver.find_element(By.XPATH, '//input[@aria-label="Select a date range."]').get_attribute('value').split()[0]
        driver.find_element(By.XPATH, '//input[@aria-label="Select a date range."]')
        while start_date != str(qdate).replace('-','/'):

            date_text = qdate.strftime("%A, %B %-d{} %Y. It's available.".format(
                    self._day_endings.get(qdate.day, "th")))

            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            sleep(2)

            driver.find_element(By.XPATH, '//input[@aria-label="Select a date range."]').click()

            while (True):
                try:
                    year = self.__get_month_year()[1]
                    break
                except Exception as ex:
                    print("get year failed")
                    raise ex
            while year != qdate.year:
                if year > qdate.year:
                    print("moving back a month - year search")
                    driver.find_element(By.XPATH, 
                        '//button[@aria-label="Previous month."]'
                    ).click()
                elif year < qdate.year:
                    print("moving forward a month - year search")
                    driver.find_element(By.XPATH, 
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
                        driver.find_element(By.XPATH, 
                            '//button[@aria-label="Previous month."]'
                        ).click()
                    else:
                        print("going forward a month - month search")
                        driver.find_element(By.XPATH, 
                            '//button[@aria-label="Next month."]'
                        ).click()
                    month = self.__get_month_year()[0]
            except Exception as ex:
                print("month search failed trying anyway")
                raise ex
            print('//div[contains(@aria-label, "{}")]'.format(date_text))
            driver.find_element(By.XPATH, '//div[contains(@aria-label, "{}")]'.format(date_text)).click()
            sleep(2)
            driver.find_element(By.XPATH, '//div[contains(@aria-label, "{}")]'.format(date_text)).click()
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return
        return

    def get_payments(self, stores, start_date, end_date):
        if isinstance(start_date, type(None)):
            start_date = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday()+14)
            )
            end_date = datetime.date.today()
        end_date = end_date - datetime.timedelta(
                days=end_date.weekday())
        results = []
        for store in stores:
            qdate = start_date
            
            try:
                while qdate < end_date:
                    print(qdate)
                    if (store == '20400' and qdate < datetime.date(2024,1,31)) or (store == '20407' and qdate < datetime.date(2024,3,18)):
                        print(f"skipping {store} {qdate}")
                    else: 
                        results.extend([self.get_payment(store, qdate)])
                    qdate = qdate + datetime.timedelta(days=7)
            finally:
                #self._driver._driver.close()
                pass
        return results

    def extract_deposit(self, driver, store, qdate):
        notes = ""
        lines = []
        # see what dates we are examining
        report_start, report_end = driver.find_element(By.XPATH, '//input[@aria-label="Select a date range."]').get_attribute('value').split("–")
        # earnings
        earnings = driver.find_element(By.XPATH, '//li[@tabindex="-1"]')
        lis = earnings.find_element(By.XPATH, '..').find_elements(By.TAG_NAME, 'li')
        lis[-2].click()
        lis[0].click()
        earnings.click()
        
        txt = earnings.find_element(By.XPATH, 
            '..').text.split('\n')
        print(txt)
        invoice = {
            txt[i]: self.convert_num(
                txt[i+1]) for i in range(0, len(txt), 2)
        }
        print(invoice)
        
        # third party
        lines.append(["1362", 'Sales', invoice['Sales']])
        
        # tips
        if 'Customer contributions' in invoice:
            lines.append(["2320", 'Customer contributions', invoice['Customer contributions']])
        if 'Customer Refunds' in invoice:
            lines.append(["4830", 'Customer Refunds',
                      invoice['Customer Refunds']])
        if 'Marketing' in invoice:
            lines.append(["6101", 'Uber Marketing', invoice['Marketing']])
        #if 'Marketplace Facilitator (MF) Tax' in invoice:
        #    lines.append(["2310", 'Marketplace Facilitator Tax', invoice['Marketplace Facilitator (MF) Tax']])
        #if 'Total Taxes' in invoice:
        #    lines.append(["1361", 'Total Taxes', invoice['Total Taxes']])
        lines.append(["6310", 'Uber fees', invoice['Uber fees']])
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
        print(report_start, report_end, qdate, qdate-datetime.timedelta(days=(qdate.weekday() - 8)))
        return result

    def get_payment(self, store, qdate=None):
        if isinstance(qdate, type(None)):
            qdate = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday() + 7)
            )
        else:
            qdate = qdate - datetime.timedelta(days=(qdate.weekday()))
        if store == '20400' and qdate < datetime.date(2024,1,31):
            qdate = datetime.date(2024,1,31)
        elif store == '20407' and qdate < datetime.date(2024,3,18):
            qdate = datetime.date(2024,3,18)
        if not self._driver:
            self._login()
        driver = self._driver._driver
        driver.get(
            "https://restaurant.uber.com/v2/payments?restaurantUUID=" +
            store_map[store]
        )
        print("**",qdate)

        qdate2 = qdate - datetime.timedelta(days=(qdate.weekday() + 7))
        if store == '20400' and qdate2 < datetime.date(2024,1,31):
            qdate2 = datetime.date(2024,1,31)
        elif store == '20407' and qdate2 < datetime.date(2024,3,7):
            qdate2 = datetime.date(2024,3,7)

        sleep(3)
        self._click_date(qdate2)
        sleep(3)
        self._click_date(qdate)
        sleep(3)

        result = self.extract_deposit(driver, store, qdate)
        return result


    def convert_num(self, number):
        if ")" in number:
            return "-" + number[2:-1]
        else:
            return number.replace('$','')

