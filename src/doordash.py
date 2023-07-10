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
             '20358': '23026026'}


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
            "https://merchant-portal.doordash.com/merchant/financials?business_id=1431"
        )

        driver.find_element(By.XPATH, 
                '//button[@data-anchor-id="TimeFrameSelector"]').click()
        driver.find_element(By.XPATH, 
                '//label[normalize-space()="Last 30 Days"]/../..'
                ).find_element(By.TAG_NAME, 'input').click()
        sleep(1)
        driver.find_element(By.XPATH, 
                '//button[normalize-space()="Apply"]').click()
        sleep(2)

        header = None
        # Payout ID, Status, Store, Payout Date, Transaction Dates,
        # Subtotal, Tax, Commission, Fees, Error Charges, Adjustments,
        # Net Payout

        for tr in driver.find_elements(By.TAG_NAME, 'tr'):
            row = []
            for td in tr.find_elements(By.TAG_NAME, 'td'):
                row.append(td.text.replace('$', '').replace('-', ''))
            if header:
                notes = json.dumps(dict(zip(header, row)))
                lines = []
                lines.append(
                    ["1260", "SUBTOTAL", row[header.index("Subtotal")]]
                )
                lines.append(
                    ["1260", "TAX_SUBTOTAL",
                    row[header.index("Tax")]]
                    )
                lines.append(
                    [
                    "6261",
                    "COMMISSION",
                    "-" + row[header.index("Commission")],
                    ]
                )
                lines.append(
                    [
                            "6260",
                            "error charges",
                            "-" + row[header.index("Error Charges")],
                        ]
                )
                lines.append(
                        [
                            "6260",
                            "adjustments",
                            # are these positive? "-" +
                            row[header.index("Adjustments")],
                        ]
                )
                lines.append(
                        [
                            "6101",
                            "marketing fees",
                            "-" + row[header.index("Fees")],
                        ]
                )
                txdate = datetime.datetime.strptime(
                            row[header.index("Payout Date")],
                            "%m/%d/%Y").date()
                pending = row[header.index("Status")] == "Pending"
                if start_date <= txdate <= end_date and not pending:
                    store = ""
                    results.append(
                            [
                                "Doordash",
                                txdate,
                                notes,
                                lines,
                                row[header.index("Store")].replace(")","")[-5:]
                            ]
                    )
            else:
                header = [x.text for x in
                            tr.find_elements(By.TAG_NAME, 'th')]
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
                            ["1260", "SUBTOTAL", row[header.index("SUBTOTAL")]]
                        )
                        lines.append(
                            ["1260", "TAX_SUBTOTAL",
                             row[header.index("TAX_SUBTOTAL")]]
                        )
                        lines.append(
                            [
                                "6261",
                                "COMMISSION",
                                "-" + row[header.index("COMMISSION")],
                            ]
                        )
                        lines.append(
                            [
                                "6260",
                                "error charges",
                                "-" + row[header.index("error charges")],
                            ]
                        )
                        lines.append(
                            [
                                "6260",
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
