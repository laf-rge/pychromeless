import csv
import datetime
import glob
import os
import re
from time import sleep
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
import qb
from ssm_parameter_store import SSMParameterStore
from webdriver_wrapper import WebDriverWrapper

"""
"""


class Crunchtime:
    """"""

    def __init__(self):
        return

    """
    """

    def _login(self, store):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._driver = WebDriverWrapper(download_location="/tmp")
        self._parameters = SSMParameterStore(prefix="/prod")["crunchtime"]
        self._driver = WebDriverWrapper(download_location="/tmp")
        driver = self._driver._driver
        driver.implicitly_wait(25)

        driver.set_page_load_timeout(45)

        driver.get("https://jerseymikes.net-chef.com/ceslogin/auto/logout.ct")
        driver.get("https://jerseymikes.net-chef.com/standalone/modern.ct#Login")
        username_element = driver.find_element(By.XPATH, '//input[@name="username"]')
        username_element.clear()
        username_element.send_keys(self._parameters["user"])
        WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        password_element = driver.find_element(By.XPATH, '//input[@name="password"]')
        password_element.clear()
        password_element.send_keys(self._parameters["password"])
        WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        driver.find_element(By.XPATH, '//button[@tabindex="3"]').click()
        WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        WebDriverWait(driver, 10).until(lambda driver: driver.switch_to.active_element == driver.find_element(By.XPATH, '//input[@name="locationId"]'))
        driver.find_element(By.XPATH, '//input[@name="locationId"]').send_keys(store)
        driver.find_element(By.XPATH, '//input[@name="locationId"]').send_keys(Keys.ENTER)
        driver.find_element(By.XPATH, '//input[@name="locationId"]').send_keys(Keys.ENTER)
        #WebDriverWait(driver, 10).until(lambda driver: driver.switch_to.active_element.tag_name == 'div')
        sleep(4)
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        return

    def get_inventory_report(self, store, year, month):
        self._login(store)
        driver = self._driver._driver
        try:
            driver.get("https://jerseymikes.net-chef.com/ncext/index.ct#inventoryMenu~actualtheoreticalcost?parentModule=inventoryMenu")
            sleep(3)
            element = driver.find_element(By.NAME, 'startDateCombo')
            loop_detection = 0
            while (loop_detection < 30 and
                   driver.switch_to.active_element.get_attribute(
                    'value') != '{0}/01/{1}'.format(
                        str(month).zfill(2), year)):
                ActionChains(driver).move_to_element(element).click().send_keys(Keys.ARROW_DOWN).send_keys(Keys.RETURN).perform()
                loop_detection += 1
            element = driver.find_element(By.NAME, "endDateCombo")
            loop_detection = 0
            while (
                    loop_detection < 30
                    and driver.find_element_by_name("endDateCombo").get_attribute(
                        "value")[:2]
                    != str(month).zfill(2)
                    and driver.find_element_by_name("endDateCombo").get_attribute(
                        "value")[6:] != year
                  ):
                ActionChains(driver).move_to_element(element).click().send_keys(Keys.ARROW_DOWN).send_keys(Keys.RETURN).perform()
                loop_detection += 1
            if loop_detection == 30:
                print(f"Valid end date not found skipping {store}")
                return
            self._export(driver, False)
        finally:
            _driver.close()

    def get_gl_report(self, store):
        self._login(store)
        driver = self._driver._driver
        try:
            driver.get(
                "https://jerseymikes.net-chef.com/ncext/index.ct#purchasingMenu~purchasesByGL?parentModule=purchasingMenu"
            )
            sleep(20)
            self._export(driver, True)
        finally:
            self._driver.close()
        return

    def _export(self, driver, export_combo):
        elem = driver.find_element(By.CSS_SELECTOR, 
            "[ces-selenium-id='toolbar_filtersBar']"
        ).find_element(By.CSS_SELECTOR, "[ces-selenium-id='button']")
        sleep(10)
        elem.click()
        sleep(6)
        export = driver.find_element(By.CSS_SELECTOR, 
            "[ces-selenium-id='tool_export']"
        )
        if export.get_attribute('data-qtip') == "Nothing to Export.":
            print("Nothing to export.")
            return
        export.click()
        # set to CSV
        element = driver.find_element(By.CSS_SELECTOR, 
            "[ces-selenium-id='combobox_exportFormat'"
        )
        element_id = "{0}-inputEl".format(element.get_property("id"))
        element.find_element(By.ID, element_id).send_keys(Keys.ARROW_DOWN)
        element.find_element(By.ID, element_id).send_keys(Keys.ARROW_DOWN)
        element.find_element(By.ID, element_id).send_keys(Keys.ARROW_DOWN)
        element.find_element(By.ID, element_id).send_keys(Keys.ENTER)
        # set export
        if export_combo:
            element = driver.find_element(By.CSS_SELECTOR, 
                "[ces-selenium-id='combobox_multiExportCombo'"
            )
            element_id = "{0}-inputEl".format(element.get_property("id"))
            element.find_element(By.ID, element_id).send_keys(Keys.ARROW_DOWN)
            element.find_element(By.ID, element_id).send_keys(Keys.ARROW_DOWN)
            element.find_element(By.ID, element_id).send_keys(Keys.ENTER)
        element.find_element(By.ID, element_id).send_keys(Keys.ENTER)
        sleep(5)

    def process_inventory_report(self, stores, year, month):
        for store in stores:
            self.get_inventory_report(store, year, month)
            filenames = glob.glob("/tmp/ActualVSTheoretical_LocationDetails_*.csv")
            if len(filenames) == 0:
                continue
            filename = filenames[0]
            with open(filename, newline="", encoding="utf-8-sig") as csvfile:
                invreader = csv.reader(csvfile)
                header = next(invreader)
                notes_header = "Information generated from CrunchTime at {0} for {1}".format(
                    header[2], header[0]
                )
                items = []
                total = 0
                for row in invreader:
                    if row[0] == 'Total Cost of Goods Sold':
                        total = row[2]
                        print(total)
                    elif row[0] == 'P&L Substructure':
                        header = row
                    elif row[0] != '' or row[1] == '':
                        continue
                    else:
                        items.append([qb.inventory_ref_lookup(
                            row[1].split()[0]),
                            row[2],
                            ", ".join(' : '.join(x) for x in zip(header,row))
                        ])
                qb.sync_inventory(year, month, items, notes_header, total, store)
            os.remove(filename)

    def process_gl_report(self, stores):
        for store in stores:
            self.get_gl_report(store)
            filenames = glob.glob("/tmp/PurchasesByGL_LocationDetails_*.csv")
            if len(filenames) == 0:
                continue
            filename = filenames[0]
            with open(filename, newline="", encoding="utf-8-sig") as csvfile:
                glreader = csv.reader(csvfile)
                header = next(glreader)
                notes_header = "Information generated from CrunchTime at {0} for {1}".format(
                    header[2], header[0]
                )
                next(glreader)  # skip header line
                items = []
                vendor = None
                invoice_num = 0
                invoice_date = None
                for row in glreader:
                    if len(row) != 3:
                        continue
                    if row[0].startswith("Invoice Number:"):
                        # clear item array
                        items = []
                        # grab invoice number information
                        i = re.split("[:\n]", row[0])
                        invoice_num = i[1].strip()
                        invoice_date = datetime.datetime.strptime(
                            re.split("[:\n]", row[1])[1].strip(), "%m/%d/%Y"
                        ).date()
                        # hotfix for paper company
                        if (
                            i[3].strip() == "WNEPLS"
                            and invoice_date.month >= 2
                            and invoice_date.day >= 28
                            and invoice_date.year >= 2020
                        ):
                            vendor = qb.vendor_lookup("PAPER")
                        elif i[3].strip() in ['20358', '20395', '20400', '20407']:
                            #hotfix for store to store
                            vendor = None
                        else:
                            vendor = qb.vendor_lookup(i[3].strip())
                        notes = notes_header + "\n" + row[2]
                        continue
                    elif row[1] == "Total: ":
                        # send invoice
                        if vendor: #skip if store to store
                            qb.sync_bill(
                                vendor, invoice_num, invoice_date, notes, items, str(store)
                            )
                        continue
                    else:
                        # map GL code to WMC accounting code
                        # add GL Description to item description
                        items.append([qb.account_ref_lookup(row[0]), row[1], row[2]])
            os.remove(filename)
