import json
import os
import io
import datetime
import calendar
import csv
import glob
import zipfile
from webdriver_wrapper import WebDriverWrapper
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from time import sleep
from bs4 import BeautifulSoup
from ssm_parameter_store import SSMParameterStore

class UberEats():
    """
    """
    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix='/prod')['ubereats']


    """
    """
    def _login(self):
        self._driver = WebDriverWrapper(download_location='/tmp')
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get("https://restaurant.uber.com/v2/payments?restaurantUUID=8d6b329b-4976-4ef7-8411-3a416614a726")
        driver.find_element_by_id('useridInput').send_keys(self._parameters['user']+Keys.RETURN)
        driver.find_element_by_id('password').send_keys(self._parameters['password']+Keys.RETURN)
        sleep(5)
        for element, pin in zip(driver.find_elements_by_xpath('//input'),self._parameters['pin']):
            element.send_keys(pin)
        driver.find_element_by_xpath('//button').click()
        sleep(10)
        return

    def get_payment(self):
        try:
            self._login()
            driver = self._driver._driver
            driver.get("https://restaurant.uber.com/v2/payments?restaurantUUID=8d6b329b-4976-4ef7-8411-3a416614a726")

            notes = ""
            lines = []

            sleep(10)

            driver.find_element_by_xpath('//div[@tabindex="0"]').click()
            txt = driver.find_element_by_xpath('//div[@tabindex="0"]').find_element_by_xpath('following-sibling::*').text.split('\n')
            lines.append(['1260',txt[0],self.convert_num(txt[1])])
            lines.append(['1260',txt[2],self.convert_num(txt[3])])
            notes += str(txt)

            driver.find_elements_by_xpath('//div[@tabindex="0"]')[1].click()
            txt = driver.find_elements_by_xpath('//div[@tabindex="0"]')[1].find_element_by_xpath('following-sibling::*').text.split('\n')
            for i in range(0, len(txt),2):
                if "Error" in txt[i]:
                    lines.append(['6260',txt[i],self.convert_num(txt[i+1])])
                else:
                    lines.append(['6261',txt[i],self.convert_num(txt[i+1])])
            notes += str(txt)

            # pay day is always Monday
            result = ['Uber Eats',
                datetime.date.today() - datetime.timedelta(days = datetime.date.today().weekday()),
                notes,
                lines,
                '20025']
            return result

        finally:
            driver.close()

    def convert_num(self, number):
        if ')' in number:
            return '-' + number[2:-1]
        else:
            return number[1:]

