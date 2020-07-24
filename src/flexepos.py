import json
import os
from webdriver_wrapper import WebDriverWrapper
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from time import sleep
from bs4 import BeautifulSoup
from ssm_parameter_store import SSMParameterStore

"""
"""
class Flexepos():
    """
    """
    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix='/prod')['flexepos']
        self._driver = WebDriverWrapper(download_location='/tmp')


    """
    """
    def _login(self):
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get("https://fms.flexepos.com/FlexeposWeb/")
        driver.find_element_by_id("login:username").clear()
        driver.find_element_by_id("login:username").send_keys(self._parameters['user'])
        driver.find_element_by_id("login:password").clear()
        driver.find_element_by_id("login:password").send_keys(self._parameters['password'])
        driver.find_element_by_name("login:j_id24").click()
        return


    """
    """
    def getDailySales(self, stores, tx_date):
        self._login()
        driver = self._driver._driver
        sales_data = {}
        store = stores[0]
        tx_date_str = tx_date.strftime("%m%d%Y")
        try:
            sales_data[store] = {}
            driver.find_element_by_id("menu:0:j_id23_header").click()
            driver.find_element_by_id("menu:0:j_id24:1:j_id25").click()
            sleep(1)
            driver.find_element_by_id("parameters:store").clear()
            driver.find_element_by_id("parameters:store").send_keys(store)
            driver.find_element_by_id("parameters:startDateCalendarInputDate").clear()
            driver.find_element_by_id("parameters:startDateCalendarInputDate").send_keys(tx_date_str)
            driver.find_element_by_id("parameters:endDateCalendarInputDate").clear()
            driver.find_element_by_id("parameters:endDateCalendarInputDate").send_keys(tx_date_str)
            checkboxes = filter( None, ("parameters:j_id{}," * 15
                         ).format(*range(68,98,2)).split(","))
            states =     [ True, False, False, False, False, False, False,
                          True, True, True, True, False, True, False, False]
            for checkbox, state in zip(map(driver.find_element_by_name, checkboxes),
                                states):
                if state != checkbox.is_selected():
                    checkbox.click()
            driver.find_element_by_id("parameters:submit").click()
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            totalsales_table = soup.find('table', attrs = { "id" : "TotalSales" })
            rows = totalsales_table.find_all('tr')
            if len(rows) != 6:
                sales_data[store]['Pre-Discount Sales'] = None 
                sales_data[store]['Discounts'] = None
                sales_data[store]['Donations'] = None
            else:
                row = [ ele.text.strip() for ele in rows[4].find_all('td') ]
                sales_data[store]['Pre-Discount Sales'] = row[3]
                sales_data[store]['Discounts'] = row[2]
                sales_data[store]['Donations'] = row[4]

            # Payment Breakdown
            payment_table = soup.find('table', attrs = { "id" : "Payments" })
            rows = payment_table.find_all('tr')
            if len(rows) != 6:
                sales_data[store]['Cash'] = None
                sales_data[store]['Check'] = None
                sales_data[store]['InStore Credit Card'] = None
                sales_data[store]['Online Credit Card'] = None
                sales_data[store]['Gift Card'] = None
                sales_data[store]['Online Gift Card'] = None
                sales_data[store]['House Account'] = None
                sales_data[store]['Remote Payment'] = None
                sales_data[store]['Third Party'] = None
            else:
                row = [ ele.text.strip() for ele in rows[4].find_all('td') ]
                sales_data[store]['Cash'] = row[1]
                sales_data[store]['Check'] = row[2]
                sales_data[store]['InStore Credit Card'] = row[3]
                sales_data[store]['Online Credit Card'] = row[4]
                sales_data[store]['Gift Card'] = row[5]
                sales_data[store]['Online Gift Card'] = row[6]
                sales_data[store]['House Account'] = row[7]
                sales_data[store]['Remote Payment'] = row[8]
                sales_data[store]['Third Party'] = row[9]

            # Collected Tax
            payment_table = soup.find('table', attrs = { "id" : "TotalTax" })
            rows = payment_table.find_all('tr')
            if len(rows) != 3:
                sales_data[store]['Sales Tax'] = None
            else:
                row = [ ele.text.strip() for ele in rows[2].find_all('td') ]
                sales_data[store]['Sales Tax'] = row[7]

            # Gift Cards Sold
            gift_cards_sold = driver.find_element_by_id("j_id318_header").text.split(":")
            sales_data[store][gift_cards_sold[0].strip()[2:]] = gift_cards_sold[1].strip()

            # Register Audit
            register_audit = driver.find_element_by_id("j_id240_header").text.split(":")
            sales_data[store][register_audit[0].strip()[2:]] = register_audit[1].strip()

            # Bank Deposits
            deposit_table = soup.find('table', attrs = {"id" : "Deposits" })
            rows = deposit_table.find_all('tr')
            sales_data[store]['Bank Deposits'] = "".join(
                [row.get_text().lstrip().replace("\n"," ").replace("   ","\n") for row in rows[1:]])

            driver.find_element_by_id("menu:0:j_id29_header").click()
            driver.find_element_by_id("menu:0:j_id30:9:j_id31").click()
            driver.find_element_by_id("parameters:submit").click()
            driver.implicitly_wait(0)
            if len(driver.find_elements_by_id("j_id86:1:j_id100:0:j_id105")) > 0:
                cctips = driver.find_element_by_id("j_id86:1:j_id100:0:j_id105").text
            else:
                cctips = driver.find_element_by_id("j_id143_body").text
            sales_data[store]['CC Tips'] = cctips
            if len(driver.find_elements_by_id("j_id111:1:j_id125:0:j_id130")) > 0:
                cctips = driver.find_element_by_id("j_id111:1:j_id125:0:j_id130").text
            else:
                cctips = driver.find_element_by_id("j_id143_body").text
            driver.implicitly_wait(5)
            sales_data[store]['Online CC Tips'] = cctips

            # get pay ins
            driver.find_element_by_id("menu:1:j_id29_switch_off").click()
            driver.find_element_by_id("menu:1:j_id30:6:j_id31").click()
            driver.find_element_by_id("parameters:types").send_keys("Payins")
            driver.find_element_by_id("parameters:submit").click()
            driver.implicitly_wait(0)
            if len(driver.find_elements_by_id("transactions")) >0 :
                payins = driver.find_element_by_id("transactions").text
            else:
                payins = driver.find_element_by_id("j_id84").text
            driver.implicitly_wait(5)
            sales_data[store]['Payins'] = payins

            # get pay outs

            if driver.find_element_by_id("j_id37_switch_off").is_displayed():
                driver.find_element_by_id("j_id37_switch_off").click()
            driver.find_element_by_id("parameters:types").send_keys("Store Payouts")
            driver.find_element_by_id("parameters:submit").click()
            driver.implicitly_wait(0)
            if len(driver.find_elements_by_id("transactions")) >0 :
                payouts = driver.find_element_by_id("transactions").text
            else:
                payouts = driver.find_element_by_id("j_id84").text
            driver.implicitly_wait(5)
            sales_data[store]['Payouts'] = payouts

        finally:
            driver.quit()
        return sales_data

    """
    """
    def getDailyJournal(self, stores, date):
        drawer_opens = {}
        try:
            self._login()
            driver = self._driver._driver
            driver.find_element_by_id("menu:1:j_id23_header").click()
            driver.find_element_by_id("menu:1:j_id24:4:j_id25").click()
            for store_number in stores:
                if driver.find_element_by_id("j_id37_switch_off").is_displayed():
                    driver.find_element_by_id("j_id37_switch_off").click()
                driver.find_element_by_id("parameters:store").clear()
                driver.find_element_by_id("parameters:store").send_keys(store_number)
                driver.find_element_by_id("parameters:startDateCalendarInputDate").click()
                driver.find_element_by_id("parameters:startDateCalendarInputDate").clear()
                driver.find_element_by_id("parameters:startDateCalendarInputDate").send_keys(date)
                driver.find_element_by_id("parameters:journalScope").click()
                Select(driver.find_element_by_id("parameters:journalScope")).select_by_visible_text("Store")
                driver.find_element_by_id("parameters:submit").click()
                driver.implicitly_wait(0)
                if len(driver.find_elements_by_id("j_id77_body")) > 0:
                    drawer_opens[store_number] = driver.find_element_by_id("j_id77_body").text
                else:
                    drawer_opens[store_number] = "No Jornal Data Found"
                driver.implicitly_wait(5)
            driver.find_element_by_id("j_id3:j_id16").click()
        finally:
            driver.quit()
        return drawer_opens

    """
    """
    def getRoyaltyReport(self, store, start_date, end_date):
        try:
            self._login()
            driver = self._driver._driver
            driver.find_element_by_id("menu:2:j_id23_header").click()
            driver.find_element_by_id("menu:2:j_id24:0:j_id25").click()
            driver.find_element_by_id("parameters:store").clear()
            driver.find_element_by_id("parameters:store").send_keys(store)
            driver.find_element_by_id("parameters:startDateCalendarInputDate").click()
            driver.find_element_by_id("parameters:startDateCalendarInputDate").clear()
            driver.find_element_by_id("parameters:startDateCalendarInputDate").send_keys(start_date.strftime("%m%d%Y"))
            driver.find_element_by_id("parameters:endDateCalendarInputDate").click()
            driver.find_element_by_id("parameters:endDateCalendarInputDate").clear()
            driver.find_element_by_id("parameters:endDateCalendarInputDate").send_keys(end_date.strftime("%m%d%Y"))
            driver.find_element_by_id("parameters:submit").click()
            driver.implicitly_wait(0)
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            royalty_table =  soup.find('table', attrs = {"id" : "RoyaltyList" })
            rows = royalty_table.find_all("tr")
            row = [ ele.text.strip() for ele in rows[1].find_all('td') ]
            return row
        finally:
            driver.quit()
