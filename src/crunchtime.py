import json
import os
import datetime
import csv
import qb
import re
import glob
from webdriver_wrapper import WebDriverWrapper
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
from ssm_parameter_store import SSMParameterStore

"""
"""
class Crunchtime():
    """
    """
    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._driver = WebDriverWrapper(download_location='/tmp')
        self._parameters = SSMParameterStore(prefix='/prod')['crunchtime']
        self._driver = WebDriverWrapper(download_location='/tmp')

        return

    """
    """
    def _login(self):
        driver = self._driver._driver
        driver.implicitly_wait(25)

        driver.set_page_load_timeout(45)

        driver.get("https://jerseymikes.net-chef.com")
        driver.find_element_by_id("username").clear()
        driver.find_element_by_id("username").send_keys(self._parameters['user'])
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys(self._parameters['password'])
        driver.find_element_by_name("login").click()
        driver.find_element_by_id("locationCoboBox-inputEl").send_keys("20025")
        driver.find_element_by_id("locationCoboBox-inputEl").send_keys(Keys.ENTER)
        sleep(2)
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        sleep(2)
        return

    """
    """
    def get_gl_report(self):
        self._login()
        driver = self._driver._driver
        try:
            driver.get("https://jerseymikes.net-chef.com/ncext/index.ct#purchasingMenu~purchasesByGL?parentModule=purchasingMenu")
            sleep(10)
            driver.find_element_by_css_selector("[ces-selenium-id='toolbar_filtersBar']").find_element_by_css_selector("[ces-selenium-id='button']").click()
            sleep(2)
            driver.find_element_by_css_selector("[ces-selenium-id='tool_export']").click()
            element = driver.find_element_by_css_selector("[ces-selenium-id='combobox_exportFormat'")
            element_id = "{0}-inputEl".format(element.get_property("id"))
            element.find_element_by_id(element_id).send_keys(Keys.ARROW_DOWN)
            element.find_element_by_id(element_id).send_keys(Keys.ARROW_DOWN)
            element.find_element_by_id(element_id).send_keys(Keys.ARROW_DOWN)
            element.find_element_by_id(element_id).send_keys(Keys.ENTER)
            element = driver.find_element_by_css_selector("[ces-selenium-id='combobox_multiExportCombo'")
            element_id = "{0}-inputEl".format(element.get_property("id"))
            element.find_element_by_id(element_id).send_keys(Keys.ARROW_DOWN)
            element.find_element_by_id(element_id).send_keys(Keys.ARROW_DOWN)
            element.find_element_by_id(element_id).send_keys(Keys.ENTER)
            element.find_element_by_id(element_id).send_keys(Keys.ENTER)
            sleep(5)
        finally:
            driver.quit()
        return

    """
    """
    def process_gl_report(self):
        self.get_gl_report()
        filename = glob.glob('/tmp/PurchasesByGL_LocationDetails_*.csv')[0]
        with open(filename,
                  newline='', encoding='utf-8-sig') as csvfile:
            glreader = csv.reader(csvfile)
            header = next(glreader)
            notes_header = "Information generated from CrunchTime at {0}".format( header[2])
            next(glreader) # skip header line
            items = []
            vendor = None
            invoice_num = 0
            invoice_date = None
            for row in glreader:
                if len(row) != 3:
                    continue
                if row[0].startswith('Invoice Number:'):
                    #clear item array
                    items = []
                    #grab invoice number information
                    i = re.split('[:\n]', row[0])
                    invoice_num = i[1].strip()
                    invoice_date = datetime.datetime.strptime(
                        re.split('[:\n]',row[1])[1].strip(),
                                               '%m/%d/%Y').date()
                    #hotfix for paper company
                    if i[3].strip() == 'WNEPLS' and invoice_date.month>=2 and invoice_date.day>=28 and invoice_date.year >=2020:
                        vendor = qb.vendor_lookup('PAPER')
                    else:
                        vendor = qb.vendor_lookup(i[3].strip())
                    notes = notes_header + "\n" + row[2]
                    continue
                elif row[1] == 'Total: ':
                    # send invoice
                    qb.sync_bill(vendor, invoice_num, invoice_date, notes,
                                 items, "20025")
                    continue
                else:
                    # map GL code to WMC accounting code
                    # add GL Description to item description
                    items.append([qb.account_ref_lookup(row[0]),row[1],row[2]])
        os.remove(filename)

