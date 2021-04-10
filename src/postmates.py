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


class Postmates():
    """
    """
    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix='/prod')['postmates']


    """
    """
    def _login(self):
        self._driver = WebDriverWrapper(download_location='/tmp')
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get("https://partner.postmates.com/dashboard/home/payments")
        driver.find_element_by_xpath('//input[@name="email"]').send_keys(self._parameters['user'])
        driver.find_element_by_xpath('//input[@name="password"]').send_keys(self._parameters['password']+Keys.ENTER)
        sleep(3)
        driver.get("https://partner.postmates.com/dashboard/home/payments")
        return

    def get_payments(self, start_date, end_date):
        try:
            self._login()
            driver = self._driver._driver

            # click calendar
            driver.find_element_by_xpath('//button[@class="button grayscale"]').click()
            # click 1 month
            driver.find_element_by_xpath('//button[@class="button grayscale"]').click()
            # click download CSV
            driver.find_elements_by_xpath('//button[@class="button button"]')[1].click()
            sleep(20)
        finally:
            driver.close()

    def process_payments(self, start_date, end_date):
        self.get_payments(start_date, end_date)
        filename = glob.glob('/tmp/Payments.csv')[0]
        results = []
        with open(filename) as f:
            preader = csv.reader(f)

            header = None

            for row in preader:
                if header:
                    notes = json.dumps(dict(zip(header,row)))
                    lines = []
                    lines.append(['1260','Total',row[header.index('Total')].strip('$')])
                    # Tax included in total
                    # lines.append(['1260','TAX_SUBTOTAL',row[header.index('TAX_SUBTOTAL')]])
                    lines.append(['6261','Commission', "-" + row[header.index('Commission')].strip('%')])
                    lines.append(['6260','Issue Adjustments', row[header.index('Issue Adjustments')].strip('$')])
                    lines.append(['6260','Dispute Adjustments', row[header.index('Dispute Adjustments')].strip('$')])
                    lines.append(['6260','Other Adjustments', row[header.index('Other Adjustments')].strip('$')])
                    lines.append(['6260','Returns', row[header.index('Returns')].strip('$')])
                    placename = { "Jersey Mike's Subs Long Beach 66790" : '20025' }
                    txdate = datetime.datetime.strptime(
                        row[header.index('\ufeffDate Paid')].split('(')[0],
                        '%a %b %d %Y %H:%M:%S %Z%z ').date()
                    if start_date <= txdate <= end_date:
                        results.append( ['Postmates',
                                   txdate,
                                   notes,
                                   lines,
                                   placename[row[header.index('Place Name')]  ] ] )
                else:
                    header=row

        os.remove(filename)
        return results






