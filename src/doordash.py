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
from selenium.common.exceptions import (NoAlertPresentException,
                                        NoSuchElementException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from ssm_parameter_store import SSMParameterStore
from webdriver_wrapper import WebDriverWrapper


class Doordash():
    """
    """
    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix='/prod')['doordash']


    """
    """
    def _login(self):
        self._driver = WebDriverWrapper(download_location='/tmp')
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get("https://merchant-portal.doordash.com/merchant/financials?store_id=631548")
        driver.find_element_by_xpath('//input[@data-anchor-id="IdentityLoginPageEmailField"]').send_keys(self._parameters['user'])
        driver.find_element_by_xpath('//input[@data-anchor-id="IdentityLoginPagePasswordField"]').send_keys(self._parameters['password'])
        driver.find_element_by_id("login-submit-button").click()
        return

    def get_payments(self, start_date, end_date):
        try:
            self._login()
            driver = self._driver._driver

            sleep(3)

            driver.find_elements_by_xpath('//button')[0].click()
            sleep(3)
            driver.find_elements_by_xpath('//button')[3].click()
            driver.find_elements_by_xpath('//input')[0].click()
            driver.find_elements_by_xpath('//input')[0].send_keys(start_date.strftime("%m/%d/%Y"))

            driver.find_element_by_xpath('//input[@placeholder="End"]').click()
            driver.find_element_by_xpath('//input[@placeholder="MM/DD/YYYY"]').send_keys(end_date.strftime("%m/%d/%Y"))

            driver.find_elements_by_xpath('//button')[-1].click()
            sleep(20)
        finally:
            driver.close()

    def process_payments(self, start_date, end_date):
        self.get_payments(start_date, end_date)
        filename = glob.glob('/tmp/summary_report_*.zip')[0]
        results = []
        with zipfile.ZipFile(filename) as z:
            directory = z.infolist()
            if len(directory) == 0 :
                print("no results in this time frame for Doordash")
                return results
            with io.TextIOWrapper(z.open(directory[0]), encoding="utf-8") as f:
                preader = csv.reader(f)

                header = None

                for row in preader:
                    if header:
                        notes = json.dumps(dict(zip(header,row)))
                        lines = []
                        lines.append(['1260','SUBTOTAL',row[header.index('SUBTOTAL')]])
                        lines.append(['1260','TAX_SUBTOTAL',row[header.index('TAX_SUBTOTAL')]])
                        lines.append(['6261','COMMISSION',"-" + row[header.index('COMMISSION')]])
                        lines.append(['6260','error charges',"-" + row[header.index('error charges')]])
                        lines.append(['6260','adjustments',"-" + row[header.index('adjustments')]])
                        results.append( ['Doordash',
                                   datetime.datetime.strptime(row[header.index('PAYOUT_DATE')], '%Y-%m-%d'),
                                   notes,
                                   lines,
                                   row[header.index('MERCHANT_STORE_ID')] ] )
                    else:
                        header=row

        os.remove(filename)
        return results






