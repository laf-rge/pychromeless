import calendar
import csv
import datetime
import glob
import io
import json
import os
import zipfile
import sys
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from ssm_parameter_store import SSMParameterStore
from webdriver_wrapper import WebDriverWrapper

store_map = {'20025': '631548',
             '20358': '23026026',
             '20395': '24923975',
             '20400': '26026815',
             '20407': '',
             }

store_inv_map = {v: k for k, v in store_map.items()}

company_id = '1431'

class Doordash:
    """"""

    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix="/prod")["doordash"]

    """
    """

    def _login(self):
        self._driver = WebDriverWrapper(download_location="/tmp")
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get(
            "https://merchant-portal.doordash.com/merchant/logout"
        )
        driver.get(
            "https://merchant-portal.doordash.com/"
        )
        driver.find_element(By.XPATH, 
            '//input[@data-anchor-id="IdentityLoginPageEmailField"]'
        ).send_keys(self._parameters["user"])
        driver.find_element(By.XPATH, 
            '//input[@data-anchor-id="IdentityLoginPagePasswordField"]'
        ).send_keys(self._parameters["password"])
        driver.find_element(By.ID, "login-submit-button").click()
        input("pause...")
        return

    def get_payments(self, stores, start_date, end_date):
        self._login()
        driver = self._driver._driver

        results = []

        
        driver.get(
            f"https://merchant-portal.doordash.com/merchant/financials?business_id={company_id}"
        )

        driver.find_element(By.XPATH, 
                '//button[@data-anchor-id="TimeFrameSelector"]').click()
        sleep(1)
        #driver.find_element(By.XPATH, 
        #        '//label[normalize-space()="Last 30 Days"]/../..'
        #        ).find_element(By.TAG_NAME, 'input').click()
        #sleep(1)
        driver.find_element(By.XPATH, 
                '//button[normalize-space()="Apply"]').click()
        sleep(2)

        payout_ids = []
        for tr in driver.find_elements(By.TAG_NAME, 'tr')[1:]:
            payout_ids.append(tr.find_elements(By.TAG_NAME, 'td')[1].find_element(By.TAG_NAME, 'a').get_attribute('href'))

        for payout_id in payout_ids:
            lines = []
            driver.get(f"{payout_id}?business_id={company_id}")
            sleep(2)

            txdate_str = driver.find_element(By.XPATH, "//*[contains(text(),'Payout on')]").text
            txdate = datetime.datetime.strptime(txdate_str, "Payout on %B %d, %Y").date()
            notes = driver.find_element(By.XPATH, "//*[starts-with(text(),'Sales')]/../../../../../../../..").text.split('\n')
            notes = {notes[i]: notes[i+1].replace('$','') for i in range(0,len(notes), 2)}
            lines.append(["1361", "Subtotal", notes['Subtotal']])
            lines.append(["1361", "Tax", notes['Tax']])
            lines.append(["6310", "DoorDash services", notes['DoorDash services']])
            lines.append(["4830", "Amendments", notes['Amendments']])
            #customer fees and customer fees tax not implemented
            
            results.append(
                [
                    "Doordash",
                    txdate,
                    str(notes),
                    lines,
                    store_inv_map[payout_id.split('/')[7]],
                ]
            )
        return results


    def get_payments_old(self, stores, start_date, end_date):
        self._login()
        driver = self._driver._driver

        results = []

        for store in stores:
            driver.get(
                "https://merchant-portal.doordash.com/merchant/financials?store_id={0}".format(store_map[store])
            )
            driver.find_element(By.XPATH, '//button[@data-anchor-id="ExportButtonDropdown"]').click()
            sleep(2)
            driver.find_element(By.XPATH, '//span[@data-anchor-id="Export Payouts"]').click()
            driver.find_elements(By.XPATH, "//input")[0].click()
            driver.find_elements(By.XPATH, "//input")[0].send_keys(
                start_date.strftime("%m/%d/%Y")
            )

            driver.find_element(By.XPATH, '//input[@placeholder="End"]').click()
            driver.find_element(By.XPATH, 
                '//input[@placeholder="MM/DD/YYYY"]'
            ).send_keys(end_date.strftime("%m/%d/%Y"))

            driver.find_elements(By.XPATH, "//button")[-1].click()
            sleep(10)
            results.extend(self._process_payments(start_date, end_date))
        return results

    def _process_payments(self, start_date, end_date):
        filename = glob.glob("/tmp/summary*.zip")[0]
        results = []
        with zipfile.ZipFile(filename) as z:
            directory = z.infolist()
            if len(directory) == 0:
                print("no results in this time frame for Doordash")
                return results
            with io.TextIOWrapper(z.open(directory[0]), encoding="utf-8") as f:
                preader = csv.reader(f)

                header = None

                for row in preader:
                    if header:
                        notes = json.dumps(dict(zip(header, row)))
                        lines = []
                        lines.append(
                            ["1361", "SUBTOTAL", row[header.index("SUBTOTAL")]]
                        )
                        lines.append(
                            ["1361", "TAX_SUBTOTAL",
                             row[header.index("TAX_SUBTOTAL")]]
                        )
                        lines.append(
                            [
                                "6310",
                                "COMMISSION",
                                "-" + row[header.index("COMMISSION")],
                            ]
                        )
                        lines.append(
                            [
                                "4830",
                                "error charges",
                                "-" + row[header.index("error charges")],
                            ]
                        )
                        lines.append(
                            [
                                "4830",
                                "adjustments",
                                # are these positive? "-" +
                                row[header.index("adjustments")],
                            ]
                        )
                        txdate = datetime.datetime.strptime(
                                 row[header.index("PAYOUT_DATE")],
                                 "%Y-%m-%d").date()
                        if start_date <= txdate <= end_date:
                            results.append(
                                [
                                    "Doordash",
                                    txdate,
                                    notes,
                                    lines,
                                    row[header.index("MERCHANT_STORE_ID")],
                                ]
                            )
                    else:
                        header = row

        os.remove(filename)
        return results
