import os
import datetime
import json
from time import sleep

from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

from ssm_parameter_store import SSMParameterStore
from webdriver_wrapper import WebDriverWrapper

class EZCater():
    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix="/prod")["ezcater"]

    def _login(self):
        self._driver = WebDriverWrapper(download_location="/tmp")
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        # logout
        # lougin
        driver.get("https://www.ezcater.com/caterer_portal/sign_in")
        driver.find_element(By.ID, "contact_username").send_keys(
            self._parameters["user"]
        )
        driver.find_element(By.ID, "contact_password").send_keys(
            self._parameters["password"] + Keys.ENTER
        )
        WebDriverWait(driver, 45)

    def get_payments(self, stores, start_date, end_date):
        self._login()
        results = []
        driver = self._driver._driver
        sleep(5)
        driver.get("https://ezmanage.ezcater.com/payments")
        WebDriverWait(driver, 45)
        apollo = driver.execute_script("return window.__APOLLO_STATE__")
        payment_ids = []
        for key in apollo.keys():
            if key.startswith("CatererVendorPayment"):
                payment_ids.append(key.split(':')[1])

        for pid in payment_ids[::-1]:
            driver.get(f"https://ezmanage.ezcater.com/payments/{pid}")
            WebDriverWait(driver, 45)
            apollo = driver.execute_script("return window.__APOLLO_STATE__")
            data = apollo[f"CatererVendorPayment:{pid}"]
            result = self.extract_deposit(data)
            if result[4] in stores and result[1] >=  start_date and result[1] <= end_date:
                results.extend([result])
            else:
                print('skipping', result[4], str(result[1]))
        return results

    def extract_deposit(self, data):
        notes = str(data)
        lines = []
        deposit_date = datetime.datetime.strptime(data["sentOn"], "%Y-%m-%d").date()

        lines.append(["1360", 'Food Total', f"{data['accountingTotals']['food']}"])
        lines.append(["2310", 'Sales Tax', f"{data['accountingTotals']['salesTax']}"])
        lines.append(["6310", 'Delivery Fees', f"{data['accountingTotals']['deliveryFees']}"])
        lines.append(["6310", 'Commission', f"-{data['accountingTotals']['marketplaceCommission']}"])
        lines.append(["2320", 'Tips', f"{data['accountingTotals']['tips']}"])
        lines.append(["6210", 'Credit Card Fees', f"-{data['accountingTotals']['creditCardFees']}"])
        lines.append(["6310", 'ezDispatch Charges & Misc. Fees', f"{data['accountingTotals']['miscFees']}"])

        result = [
            "EZ Cater",
            deposit_date,
            notes,
            lines,
            data['name'].split('#')[1][:5],
        ]
        return result

