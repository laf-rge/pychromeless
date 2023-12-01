import calendar
import datetime
import json
import os
from time import sleep

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

from ssm_parameter_store import SSMParameterStore
from webdriver_wrapper import WebDriverWrapper
from functools import partial

"""
"""

onDay = lambda weekdate, weekday: weekdate + datetime.timedelta(days=(weekday-weekdate.weekday())%7)

class Flexepos:
    """"""

    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix="/prod")["flexepos"]

    """
    """

    def _login(self):
        self._driver = WebDriverWrapper(download_location="/tmp")
        driver = self._driver._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)
        driver.get('https://fms.flexepos.com/FlexeposWeb/login.seam?actionMethod=home.xhtml%3Auser.clear')
        driver.get("https://fms.flexepos.com/FlexeposWeb/")
        sleep(5)
        driver.find_element(By.ID, "login:username").clear()
        driver.find_element(By.ID, "login:username").send_keys(self._parameters["user"])
        driver.find_element(By.ID, "login:password").clear()
        driver.find_element(By.ID, "login:password").send_keys(
            self._parameters["password"] + Keys.ENTER
        )
        return

    """
    """

    def getOnlinePayments(self, stores, year, month):
        span_dates = [
            datetime.date(year, month, 1),
            datetime.date(year, month, calendar.monthrange(year, month)[1])
        ]
        span_date_start = span_dates[0].strftime("%m%d%Y")
        span_date_end = span_dates[1].strftime("%m%d%Y")

        self._login()
        driver = self._driver._driver

        payment_data = {}

        try:
            sleep(2)
            driver.find_element(By.ID, "menu:2:j_id23_header").click()
            sleep(2)
            driver.find_element(By.ID, "menu:2:j_id24:1:j_id25").click()
            sleep(1)
            for store in stores:
                payment_data[store] = {}
                sleep(3)
                driver.find_element(By.ID, "parameters:store").clear()
                driver.find_element(By.ID, "parameters:store").send_keys(store)
                driver.find_element(By.ID, "parameters:startDateCalendarInputDate").clear()
                driver.find_element(By.ID, 
                    "parameters:startDateCalendarInputDate"
                ).send_keys(span_date_start)
                driver.find_element(By.ID, "parameters:endDateCalendarInputDate").clear()
                driver.find_element(By.ID, "parameters:endDateCalendarInputDate").send_keys(
                    span_date_end
                )
                driver.find_element(By.ID, "parameters:submit").click()
                sleep(5)
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                online_table = soup.find("table", attrs={"id": "onlineOrdersList"})
                if not online_table:
                    payment_data.pop(store, None)
                    continue
                rows = online_table.find_all("tr")
                if len(rows) != 2:
                    payment_data[store]["Tendered"] = None
                    payment_data[store]["Tip"] = None
                    payment_data[store]["Total"] = None
                    payment_data[store]["Interchange Fee"] = None
                    payment_data[store]["Patent Fee"] = None
                    payment_data[store]["ECommerce Fee"] = None
                    payment_data[store]["Total Fees"] = None
                else:
                    row = [ele.text.strip() for ele in rows[1].find_all("td")]
                    payment_data[store]["Tendered"] = row[1]
                    payment_data[store]["Tip"] = row[2]
                    payment_data[store]["Total"] = row[3]
                    payment_data[store]["Interchange Fee"] = row[4]
                    payment_data[store]["Patent Fee"] = row[5]
                    payment_data[store]["ECommerce Fee"] = row[6]
                    payment_data[store]["Total Fees"] = row[7]
                driver.find_element(By.ID, "j_id37_switch_off").click()
        finally:
            if driver:
                driver.quit()

        return payment_data

    """
    """

    def getDailySales(self, stores, tx_date):
        self._login()
        driver = self._driver._driver
        sales_data = {}
        tx_date_str = tx_date.strftime("%m%d%Y")
        try:
            for store in stores:
                driver.get("https://fms.flexepos.com/FlexeposWeb/home.seam")
                sales_data[store] = {}
                driver.find_element(By.ID, "menu:0:j_id23_header").click()
                driver.find_element(By.ID, "menu:0:j_id24:1:j_id25").click()
                sleep(1)
                driver.find_element(By.ID, "parameters:store").clear()
                driver.find_element(By.ID, "parameters:store").send_keys(store)
                driver.find_element(By.ID, "parameters:startDateCalendarInputDate").clear()
                driver.find_element(By.ID, 
                    "parameters:startDateCalendarInputDate"
                ).send_keys(tx_date_str)
                driver.find_element(By.ID, "parameters:endDateCalendarInputDate").clear()
                driver.find_element(By.ID, "parameters:endDateCalendarInputDate").send_keys(
                    tx_date_str
                )
                checkboxes = filter(
                    None, ("parameters:j_id{}," * 15).format(*range(68, 98, 2)).split(",")
                )
                states = [
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    True,
                    True,
                    True,
                    True,
                    False,
                    True,
                    False,
                    False,
                ]
                for checkbox, state in zip(
                    map(partial(driver.find_element, By.NAME), checkboxes), states
                ):
                    if state != checkbox.is_selected():
                        checkbox.click()
                driver.find_element(By.ID, "parameters:submit").click()
                sleep(4)
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                totalsales_table = soup.find("table", attrs={"id": "TotalSales"})
                rows = totalsales_table.find_all("tr")
                if len(rows) != 6:
                    sales_data[store]["Pre-Discount Sales"] = None
                    sales_data[store]["Discounts"] = None
                    sales_data[store]["Donations"] = None
                else:
                    row = [ele.text.strip() for ele in rows[4].find_all("td")]
                    sales_data[store]["Pre-Discount Sales"] = row[3]
                    sales_data[store]["Discounts"] = row[2]
                    sales_data[store]["Donations"] = row[4]

                # Payment Breakdown
                payment_table = soup.find("table", attrs={"id": "Payments"})
                rows = payment_table.find_all("tr")
                if len(rows) != 6:
                    sales_data[store]["Cash"] = None
                    sales_data[store]["Check"] = None
                    sales_data[store]["InStore Credit Card"] = None
                    sales_data[store]["Online Credit Card"] = None
                    sales_data[store]["Gift Card"] = None
                    sales_data[store]["Online Gift Card"] = None
                    sales_data[store]["House Account"] = None
                    sales_data[store]["Remote Payment"] = None
                    sales_data[store]["Third Party"] = None
                else:
                    row = [ele.text.strip() for ele in rows[4].find_all("td")]
                    sales_data[store]["Cash"] = row[1]
                    sales_data[store]["Check"] = row[2]
                    sales_data[store]["InStore Credit Card"] = row[3]
                    sales_data[store]["Online Credit Card"] = row[4]
                    sales_data[store]["Gift Card"] = row[5]
                    sales_data[store]["Online Gift Card"] = row[6]
                    sales_data[store]["House Account"] = row[7]
                    sales_data[store]["Remote Payment"] = row[8]
                    sales_data[store]["Third Party"] = row[9]

                # Collected Tax
                payment_table = soup.find("table", attrs={"id": "TotalTax"})
                rows = payment_table.find_all("tr")
                if len(rows) != 3:
                    sales_data[store]["Sales Tax"] = None
                else:
                    row = [ele.text.strip() for ele in rows[2].find_all("td")]
                    sales_data[store]["Sales Tax"] = row[7]

                # Gift Cards Sold
                gift_cards_sold = driver.find_element(By.ID, "j_id318_header").text.split(
                    ":"
                )
                sales_data[store][gift_cards_sold[0].strip()[2:]] = gift_cards_sold[
                    1
                ].strip()

                # Register Audit
                register_audit = driver.find_element(By.ID, "j_id240_header").text.split(":")
                sales_data[store][register_audit[0].strip()[2:]] = register_audit[1].strip()

                # Bank Deposits
                deposit_table = soup.find("table", attrs={"id": "Deposits"})
                rows = deposit_table.find_all("tr")
                sales_data[store]["Bank Deposits"] = "".join(
                    [
                        row.get_text().lstrip().replace("\n", " ").replace("   ", "\n")
                        for row in rows[1:]
                    ]
                )

                driver.find_element(By.ID, "menu:0:j_id29_header").click()
                driver.find_element(By.ID, "menu:0:j_id30:9:j_id31").click()
                driver.find_element(By.ID, "parameters:submit").click()
                driver.implicitly_wait(10)
                if len(driver.find_elements(By.ID, "j_id86:1:j_id100:0:j_id105")) > 0:
                    cctips = driver.find_element(By.ID, "j_id86:1:j_id100:0:j_id105").text
                else:
                    cctips = driver.find_element(By.ID, "j_id143_body").text
                sales_data[store]["CC Tips"] = cctips
                if len(driver.find_elements(By.ID, "j_id111:1:j_id125:0:j_id130")) > 0:
                    cctips = driver.find_element(By.ID, "j_id111:1:j_id125:0:j_id130").text
                else:
                    cctips = driver.find_element(By.ID, "j_id143_body").text
                driver.implicitly_wait(5)
                sales_data[store]["Online CC Tips"] = cctips

                # get pay ins
                driver.find_element(By.ID, "menu:1:j_id29_switch_off").click()
                driver.find_element(By.ID, "menu:1:j_id30:6:j_id31").click()
                driver.find_element(By.ID, "parameters:types").send_keys("Payins")
                driver.find_element(By.ID, "parameters:submit").click()
                driver.implicitly_wait(0)
                # input('pause')
                sleep(2)
                if len(driver.find_elements(By.ID, "transactions")) > 0:
                    payins = driver.find_element(By.ID, "transactions").text
                else:
                    payins = driver.find_element(By.ID, "j_id84").text
                driver.implicitly_wait(5)
                sales_data[store]["Payins"] = payins

                # get pay outs

                if driver.find_element(By.ID, "j_id37_switch_off").is_displayed():
                    driver.find_element(By.ID, "j_id37_switch_off").click()
                driver.find_element(By.ID, "parameters:types").send_keys("Store Payouts")
                driver.find_element(By.ID, "parameters:submit").click()
                driver.implicitly_wait(0)
                if len(driver.find_elements(By.ID, "transactions")) > 0:
                    payouts = driver.find_element(By.ID, "transactions").text
                else:
                    payouts = driver.find_element(By.ID, "j_id84").text
                driver.implicitly_wait(5)
                sales_data[store]["Payouts"] = payouts

        finally:
            if driver:
                driver.quit()
            pass
        return sales_data

    """
    """

    def getDailyJournal(self, stores, qdate):
        drawer_opens = {}
        driver = None
        try:
            self._login()
            driver = self._driver._driver
            driver.set_page_load_timeout(60)
            sleep(2)
            driver.find_element(By.ID, "menu:1:j_id23_header").click()
            sleep(2)
            driver.find_element(By.ID, "menu:1:j_id24:4:j_id25").click()
            for store_number in stores:
                sleep(2)
                if driver.find_element(By.ID, "j_id37_switch_off").is_displayed():
                    driver.find_element(By.ID, "j_id37_switch_off").click()
                driver.find_element(By.ID, "parameters:store").clear()
                driver.find_element(By.ID, "parameters:store").send_keys(store_number)
                driver.find_element(By.ID, 
                    "parameters:startDateCalendarInputDate"
                ).click()
                driver.find_element(By.ID, 
                    "parameters:startDateCalendarInputDate"
                ).clear()
                driver.find_element(By.ID, 
                    "parameters:startDateCalendarInputDate"
                ).send_keys(qdate)
                driver.find_element(By.ID, "parameters:journalScope").click()
                Select(
                    driver.find_element(By.ID, "parameters:journalScope")
                ).select_by_visible_text("Store")
                driver.find_element(By.ID, "parameters:submit").click()
                WebDriverWait(driver, 45)
                if len(driver.find_elements(By.ID, "j_id78_body")) > 0:
                    drawer_opens[store_number] = driver.find_element(By.ID, 
                        "j_id78_body"
                    ).text
                else:
                    drawer_opens[store_number] = "No Jornal Data Found"
                driver.implicitly_wait(5)
            driver.find_element(By.ID, "j_id3:j_id16").click()
        finally:
            if driver:
                driver.quit()
        return drawer_opens

    """
    """

    def getTips(self, stores, start_date, end_date):
        rv = {}
        driver = None
        try:
            self._login()
            driver = self._driver._driver
            driver.find_element(By.ID, "menu:0:j_id23_header").click()
            driver.find_element(By.ID, "menu:0:j_id24:18:j_id25").click()
            for store in stores:    
                driver.find_element(By.ID, "parameters:store").clear()
                driver.find_element(By.ID, "parameters:store").send_keys(store)
                driver.find_element(By.ID, "parameters:startDateCalendarInputDate").click()
                driver.find_element(By.ID, "parameters:startDateCalendarInputDate").clear()
                driver.find_element(By.ID, 
                    "parameters:startDateCalendarInputDate"
                ).send_keys(start_date.strftime("%m%d%Y"))
                driver.find_element(By.ID, "parameters:endDateCalendarInputDate").click()
                driver.find_element(By.ID, "parameters:endDateCalendarInputDate").clear()
                driver.find_element(By.ID, "parameters:endDateCalendarInputDate").send_keys(
                    end_date.strftime("%m%d%Y")
                )
                driver.find_element(By.ID, "parameters:submit").click()
                driver.implicitly_wait(0)
                sleep(8)
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                tips_table = soup.find("table", attrs={"id": "j_id78"})
                rows = tips_table.find_all("tr")
                rv[store] = [[ele.text.strip() for ele in rows[0].find_all('th')[1:]],
                            [float(x.text.strip()) for x in rows[1].find_all('td')[1:]]]
                
        finally:
            if driver:
                driver.quit()
        return rv

    """
    """
    def getRoyaltyReport(self, group, start_date, end_date):
        royalty_data = {}
        driver = None
        try:
            self._login()
            driver = self._driver._driver
            sleep(2)
            driver.find_element(By.ID, "menu:2:j_id23_header").click()
            sleep(2)
            driver.find_element(By.ID, "menu:2:j_id24:0:j_id25").click()
            driver.find_element(By.ID, "search:searchType:1").click()
            driver.find_element(By.ID, "parameters:group").clear()
            driver.find_element(By.ID, "parameters:group").send_keys(group)
            sleep(2)
            driver.find_element(By.ID, "parameters:startDateCalendarInputDate").click()
            driver.find_element(By.ID, "parameters:startDateCalendarInputDate").clear()
            driver.find_element(By.ID, 
                "parameters:startDateCalendarInputDate"
            ).send_keys(start_date.strftime("%m%d%Y"))
            driver.find_element(By.ID, "parameters:endDateCalendarInputDate").click()
            driver.find_element(By.ID, "parameters:endDateCalendarInputDate").clear()
            driver.find_element(By.ID, "parameters:endDateCalendarInputDate").send_keys(
                end_date.strftime("%m%d%Y")
            )
            driver.find_element(By.ID, "parameters:submit").click()
            driver.implicitly_wait(0)
            sleep(8)
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            royalty_table = soup.find("table", attrs={"id": "RoyaltyList"})
            rows = royalty_table.find_all("tr")[1:-1]
            for row_html in rows:
                row = [ele.text.strip() for ele in row_html.find_all("td")]
                royalty_data[row[0]] = {
                        "Net Sales": row[1],
                        "Royalty": row[2],
                        "Advertising": row[4],
                        "CoOp": "0",
                        "Media": row[6],
                    }
            return royalty_data
        finally:
            if driver:
                driver.quit()
    
    """
    The gift card periods are Thursday to Wednesday with funding on Friday's. Comparing your 
    debits/credits each Friday with the GC report on Flexepos should help you reconcile.

    You are including the online gift cards. Online payments are paid by Anne Sheehan in the 
    corporate accounting department (copied). Tickets with “99” are online/app orders.

    Online credit card and gift card payments are an ACH transaction made by the corporate 
    office. So, yes, any tickets with a “00” in the middle are online tickets.
    
    The $12.50 are monthly fees.

    using the gift card report in Flexepos

    Add the instore amounts minus the gift cards redeemed. 

    Should the online ammount get minused from the JM online deposit?
    No, since the online gift card entry is charged minus to online credit card   
    [ store, txdate, sold, instore, online]
    """
    def getGiftCardACH(self, stores, start_date, end_date):
        if end_date <= start_date:
            raise Exception("End date can not be before start date.")
        
        try:
            self._login()
            driver = self._driver._driver
            # navigate to gift card report
            sleep(2)
            driver.find_element(By.ID, "menu:0:j_id23_header").click()
            sleep(2)
            driver.find_element(By.ID, "menu:0:j_id24:10:j_id25").click()
            sleep(2)
            step_date = onDay(start_date, 4) #always Friday
            results = []
            while step_date < end_date:
                period_end= step_date - datetime.timedelta(days=2)
                period_start = period_end - datetime.timedelta(days=6)
                for store in stores:
                    notes = str(datetime.date.today())
                    lines = []
                    search_ele = driver.find_element(By.ID, "j_id37_body")
                    if not search_ele.is_displayed():
                        driver.find_element(By.ID, "j_id37_header").click()
                        
                    driver.find_element(By.ID, "parameters:store").clear()
                    driver.find_element(By.ID, "parameters:store").send_keys(store)
                    driver.find_element(By.ID, "parameters:startDateCalendarInputDate").click()
                    driver.find_element(By.ID, "parameters:startDateCalendarInputDate").clear()
                    driver.find_element(By.ID, 
                        "parameters:startDateCalendarInputDate"
                    ).send_keys(period_start.strftime("%m%d%Y"))
                    driver.find_element(By.ID, "parameters:endDateCalendarInputDate").click()
                    driver.find_element(By.ID, "parameters:endDateCalendarInputDate").clear()
                    driver.find_element(By.ID, "parameters:endDateCalendarInputDate").send_keys(
                        period_end.strftime("%m%d%Y")
                    )
                    
                    Select(driver.find_element(By.ID, 'parameters:GroupByList')).select_by_index(1)
                    driver.find_element(By.ID, "parameters:submit").click()
                    driver.implicitly_wait(0)
                    sleep(8) 
                    soup = BeautifulSoup(driver.page_source, features="html.parser")
                   
                    giftcardsales = soup.find("table" , attrs={"id": "j_id125"})
                    if giftcardsales:
                        lines.append(["1330", "sold", "-" + giftcardsales.find_all("tr")[4].find_all("td")[2].text.strip()])
                    giftcardredeemed = soup.find("table" , attrs={"id": "j_id176"})
                    
                    if giftcardredeemed:
                        lines.append(["1330", "instore", giftcardredeemed.find_all("tr")[1].find_all("td")[-3].text.strip()])               
                    if len(lines) > 0:
                        results.append(["Jersey Mikes Franchise System", step_date, notes, lines, store])
                step_date = step_date + datetime.timedelta(days=7)
            return results
        finally:
            if driver:
                driver.quit()

    def getDailyJournalExport(self, stores, start_date, end_date):
        qdate = end_date
        while qdate >= start_date:
            try:
                daily_journal = self.getDailyJournal(stores, qdate.strftime("%m%d%Y"))
            except Exception as ex:
                print(ex)
                sleep(1)
                continue
            for store in stores:
                with open("/Users/wgreen/Google Drive/Shared drives/Wagoner Management Corp./Sales Tax/Journal/{0}-{1}_daily_journal.txt".format(str(qdate), store), "w") as fileout:
                    fileout.write(daily_journal[store])
            qdate = qdate - datetime.timedelta(days = 1)

