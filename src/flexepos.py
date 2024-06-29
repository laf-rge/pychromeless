import calendar
import datetime
import os
from functools import partial
from time import sleep
from typing import cast

from bs4 import BeautifulSoup, Tag
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from ssm_parameter_store import SSMParameterStore
from webdriver import initialise_driver


# Tag IDs dictionary
TAG_IDS = {
    "login_username": "login:username",
    "login_password": "login:password",
    "menu_header_root": "menu:{}:j_id23_header",
    "menu_header": "menu:{}:j_id29_header",
    "menu_item_root": "menu:{}:j_id24:{}:j_id25",
    "menu_item": "menu:{}:j_id30:{}:j_id31",
    "parameters_store": "parameters:store",
    "parameters_group": "parameters:group",
    "start_date": "parameters:startDateCalendarInputDate",
    "end_date": "parameters:endDateCalendarInputDate",
    "group_by": "parameters:GroupById",
    "submit": "parameters:submit",
    "types": "parameters:types",
    "switch_off": "j_id37_switch_off",
    "online_orders_list": "onlineOrdersList",
    "total_sales": "TotalSales",
    "payments": "Payments",
    "total_tax": "TotalTax",
    "gift_cards_sold": "j_id318_header",
    "register_audit": "j_id240_header",
    "deposits": "Deposits",
    "cc_tips_1": "j_id86:1:j_id100:0:j_id105",
    "cc_tips_2": "j_id143_body",
    "online_cc_tips_1": "j_id111:1:j_id125:0:j_id130",
    "online_cc_tips_2": "j_id143_body",
    "transactions": "transactions",
    "journal_scope": "parameters:journalScope",
    "royalty_list": "RoyaltyList",
    "gift_card_sales": "j_id125",
    "gift_card_redeemed": "j_id176",
}


def onDay(weekdate, weekday):
    return weekdate + datetime.timedelta(days=(weekday - weekdate.weekday()) % 7)


class Flexepos:
    """"""

    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = cast(
            SSMParameterStore, SSMParameterStore(prefix="/prod")["flexepos"]
        )

    """
    """

    def _login(self):
        self._driver = initialise_driver()
        driver = self._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)
        driver.get(
            "https://fms.flexepos.com/FlexeposWeb/login.seam?actionMethod=home.xhtml%3Auser.clear"
        )
        driver.get("https://fms.flexepos.com/FlexeposWeb/")
        sleep(5)
        driver.find_element(By.ID, TAG_IDS["login_username"]).clear()
        driver.find_element(By.ID, TAG_IDS["login_username"]).send_keys(
            str(self._parameters["user"])
        )
        driver.find_element(By.ID, TAG_IDS["login_password"]).clear()
        driver.find_element(By.ID, TAG_IDS["login_password"]).send_keys(
            str(self._parameters["password"]) + Keys.ENTER
        )
        return

    def getThirdPartyTransactions(self, stores, year, month):
        span_dates = [
            datetime.date(year, month, 1),
            datetime.date(year, month, calendar.monthrange(year, month)[1]),
        ]
        span_date_start = span_dates[0].strftime("%m%d%Y")
        span_date_end = span_dates[1].strftime("%m%d%Y")

        self._login()
        driver = self._driver

        payment_data = {}

        try:
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_header_root"].format(0)).click()
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_item_root"].format(0, 13)).click()
            sleep(1)
            for store in stores:
                payment_data[store] = {}
                sleep(3)
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).clear()
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).send_keys(store)
                driver.find_element(By.ID, TAG_IDS["start_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["start_date"]).send_keys(
                    span_date_start
                )
                driver.find_element(By.ID, TAG_IDS["end_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["end_date"]).send_keys(span_date_end)
                driver.find_element(By.ID, TAG_IDS["group_by"]).click()
                Select(
                    driver.find_element(By.ID, TAG_IDS["group_by"])
                ).select_by_visible_text("Summary")
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                sleep(5)
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                online_table = soup.find("table", attrs={"class": "table-standard"})
                if not online_table or not isinstance(online_table, Tag):
                    payment_data.pop(store, None)
                    continue
                rows = online_table.find_all("tr")
                for row in rows[1:]:
                    r = [ele.text.strip() for ele in row.find_all("td")]
                    payment_data[store][r[0]] = r[4]
                driver.find_element(By.ID, TAG_IDS["switch_off"]).click()
        finally:
            if driver:
                self._driver.close()

        return payment_data

    """
    """

    def getOnlinePayments(self, stores, year, month):
        span_dates = [
            datetime.date(year, month, 1),
            datetime.date(year, month, calendar.monthrange(year, month)[1]),
        ]
        span_date_start = span_dates[0].strftime("%m%d%Y")
        span_date_end = span_dates[1].strftime("%m%d%Y")

        self._login()
        driver = self._driver

        payment_data = {}

        try:
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_header_root"].format(2)).click()
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_item_root"].format(2, 1)).click()
            sleep(1)
            for store in stores:
                payment_data[store] = {}
                sleep(3)
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).clear()
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).send_keys(store)
                driver.find_element(By.ID, TAG_IDS["start_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["start_date"]).send_keys(
                    span_date_start
                )
                driver.find_element(By.ID, TAG_IDS["end_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["end_date"]).send_keys(span_date_end)
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                sleep(5)
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                online_table = soup.find(
                    "table", attrs={"id": TAG_IDS["online_orders_list"]}
                )
                if not online_table or not isinstance(online_table, Tag):
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
                driver.find_element(By.ID, TAG_IDS["switch_off"]).click()
        finally:
            if driver:
                self._driver.close()

        return payment_data

    """
    """

    def getDailySales(self, stores, tx_date):
        self._login()
        driver = self._driver
        sales_data = {}
        tx_date_str = tx_date.strftime("%m%d%Y")
        try:
            for store in stores:
                driver.get("https://fms.flexepos.com/FlexeposWeb/home.seam")
                sales_data[store] = {}
                driver.find_element(
                    By.ID, TAG_IDS["menu_header_root"].format(0)
                ).click()
                driver.find_element(
                    By.ID, TAG_IDS["menu_item_root"].format(0, 1)
                ).click()
                sleep(1)
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).clear()
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).send_keys(store)
                driver.find_element(By.ID, TAG_IDS["start_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["start_date"]).send_keys(tx_date_str)
                driver.find_element(By.ID, TAG_IDS["end_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["end_date"]).send_keys(tx_date_str)
                checkboxes = filter(
                    None,
                    ("parameters:j_id{}," * 15).format(*range(68, 98, 2)).split(","),
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
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                sleep(4)
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                totalsales_table = soup.find(
                    "table", attrs={"id": TAG_IDS["total_sales"]}
                )
                if not totalsales_table or not isinstance(totalsales_table, Tag):
                    continue
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
                payment_table = soup.find("table", attrs={"id": TAG_IDS["payments"]})
                if not payment_table or not isinstance(payment_table, Tag):
                    continue
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

                # Collected Tax
                payment_table = soup.find("table", attrs={"id": TAG_IDS["total_tax"]})
                if not payment_table or not isinstance(payment_table, Tag):
                    continue
                rows = payment_table.find_all("tr")
                if len(rows) != 3:
                    sales_data[store]["Sales Tax"] = None
                else:
                    row = [ele.text.strip() for ele in rows[2].find_all("td")]
                    sales_data[store]["Sales Tax"] = row[7]

                # Gift Cards Sold
                gift_cards_sold = driver.find_element(
                    By.ID, TAG_IDS["gift_cards_sold"]
                ).text.split(":")
                sales_data[store][gift_cards_sold[0].strip()[2:]] = gift_cards_sold[
                    1
                ].strip()

                # Register Audit
                register_audit = driver.find_element(
                    By.ID, TAG_IDS["register_audit"]
                ).text.split(":")
                sales_data[store][register_audit[0].strip()[2:]] = register_audit[
                    1
                ].strip()

                # Bank Deposits
                deposit_table = soup.find("table", attrs={"id": TAG_IDS["deposits"]})
                if not deposit_table or not isinstance(deposit_table, Tag):
                    continue
                rows = deposit_table.find_all("tr")
                sales_data[store]["Bank Deposits"] = "".join(
                    [
                        row.get_text().lstrip().replace("\n", " ").replace("   ", "\n")
                        for row in rows[1:]
                    ]
                )

                driver.find_element(By.ID, TAG_IDS["menu_header"].format(0)).click()
                driver.find_element(By.ID, TAG_IDS["menu_item"].format(0, 9)).click()
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                driver.implicitly_wait(10)
                if len(driver.find_elements(By.ID, TAG_IDS["cc_tips_1"])) > 0:
                    cctips = driver.find_element(By.ID, TAG_IDS["cc_tips_1"]).text
                else:
                    cctips = driver.find_element(By.ID, TAG_IDS["cc_tips_2"]).text
                sales_data[store]["CC Tips"] = cctips
                if len(driver.find_elements(By.ID, TAG_IDS["online_cc_tips_1"])) > 0:
                    cctips = driver.find_element(
                        By.ID, TAG_IDS["online_cc_tips_1"]
                    ).text
                else:
                    cctips = driver.find_element(
                        By.ID, TAG_IDS["online_cc_tips_2"]
                    ).text
                driver.implicitly_wait(5)
                sales_data[store]["Online CC Tips"] = cctips

                # get pay ins
                driver.find_element(By.ID, TAG_IDS["menu_header"].format(1)).click()
                driver.find_element(By.ID, TAG_IDS["menu_item"].format(1, 6)).click()
                driver.find_element(By.ID, TAG_IDS["types"]).send_keys("Payins")
                self.setDateRange(driver, tx_date_str)
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                driver.implicitly_wait(0)
                sleep(2)
                if len(driver.find_elements(By.ID, TAG_IDS["transactions"])) > 0:
                    payins = driver.find_element(By.ID, TAG_IDS["transactions"]).text
                else:
                    payins = driver.find_element(By.ID, "j_id84").text
                driver.implicitly_wait(5)
                sales_data[store]["Payins"] = payins

                # get pay outs
                if driver.find_element(By.ID, TAG_IDS["switch_off"]).is_displayed():
                    driver.find_element(By.ID, TAG_IDS["switch_off"]).click()
                driver.find_element(By.ID, TAG_IDS["types"]).send_keys("Store Payouts")
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                driver.implicitly_wait(0)
                if len(driver.find_elements(By.ID, TAG_IDS["transactions"])) > 0:
                    payouts = driver.find_element(By.ID, TAG_IDS["transactions"]).text
                else:
                    payouts = driver.find_element(By.ID, "j_id84").text
                driver.implicitly_wait(5)
                sales_data[store]["Payouts"] = payouts

                # break down third party
                driver.find_element(By.ID, TAG_IDS["menu_header"].format(0)).click()
                sleep(2)
                driver.find_element(By.ID, TAG_IDS["menu_item"].format(0, 13)).click()
                sleep(1)
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).clear()
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).send_keys(store)
                self.setDateRange(driver, tx_date_str)
                driver.find_element(By.ID, TAG_IDS["group_by"]).click()
                Select(
                    driver.find_element(By.ID, TAG_IDS["group_by"])
                ).select_by_visible_text("Summary")
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                sleep(5)
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                online_table = soup.find("table", attrs={"class": "table-standard"})
                if online_table and isinstance(online_table, Tag):
                    rows = online_table.find_all("tr")
                    for row in rows[1:-1]:
                        r = [ele.text.strip() for ele in row.find_all("td")]
                        sales_data[store][r[0]] = r[4]
        finally:
            if driver:
                self._driver.close()
        return sales_data

    def setDateRange(self, driver, tx_date_str):
        driver.find_element(By.ID, TAG_IDS["start_date"]).clear()
        driver.find_element(By.ID, TAG_IDS["start_date"]).send_keys(tx_date_str)
        driver.find_element(By.ID, TAG_IDS["end_date"]).clear()
        driver.find_element(By.ID, TAG_IDS["end_date"]).send_keys(tx_date_str)

    """
    """

    def getDailyJournal(self, stores, qdate):
        drawer_opens = {}
        driver = None
        try:
            self._login()
            driver = self._driver
            driver.set_page_load_timeout(60)
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_header_root"].format(1)).click()
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_item_root"].format(1, 4)).click()
            for store_number in stores:
                sleep(2)
                if driver.find_element(By.ID, TAG_IDS["switch_off"]).is_displayed():
                    driver.find_element(By.ID, TAG_IDS["switch_off"]).click()
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).clear()
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).send_keys(
                    store_number
                )
                driver.find_element(By.ID, TAG_IDS["start_date"]).click()
                driver.find_element(By.ID, TAG_IDS["start_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["start_date"]).send_keys(qdate)
                driver.find_element(By.ID, TAG_IDS["journal_scope"]).click()
                Select(
                    driver.find_element(By.ID, TAG_IDS["journal_scope"])
                ).select_by_visible_text("Store")
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                WebDriverWait(driver, 45)
                if len(driver.find_elements(By.ID, "j_id78_body")) > 0:
                    drawer_opens[store_number] = driver.find_element(
                        By.ID, "j_id78_body"
                    ).text
                else:
                    drawer_opens[store_number] = "No Jornal Data Found"
                driver.implicitly_wait(5)
            driver.find_element(By.ID, "j_id3:j_id16").click()
        finally:
            if driver:
                self._driver.close()
        return drawer_opens

    """
    """

    def getTips(self, stores, start_date, end_date):
        rv = {}
        driver = None
        try:
            self._login()
            driver = self._driver
            driver.find_element(By.ID, TAG_IDS["menu_header_root"].format(0)).click()
            driver.find_element(By.ID, TAG_IDS["menu_item_root"].format(0, 18)).click()
            for store in stores:
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).clear()
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).send_keys(store)
                driver.find_element(By.ID, TAG_IDS["start_date"]).click()
                driver.find_element(By.ID, TAG_IDS["start_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["start_date"]).send_keys(
                    start_date.strftime("%m%d%Y")
                )
                driver.find_element(By.ID, TAG_IDS["end_date"]).click()
                driver.find_element(By.ID, TAG_IDS["end_date"]).clear()
                driver.find_element(By.ID, TAG_IDS["end_date"]).send_keys(
                    end_date.strftime("%m%d%Y")
                )
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                driver.implicitly_wait(0)
                sleep(8)
                soup = BeautifulSoup(driver.page_source, features="html.parser")
                tips_table = soup.find("table", attrs={"id": "j_id78"})
                if tips_table and isinstance(tips_table, Tag):
                    rows = tips_table.find_all("tr")
                    rv[store] = [
                        [ele.text.strip() for ele in rows[0].find_all("th")[1:]],
                        [float(x.text.strip()) for x in rows[1].find_all("td")[1:]],
                    ]

        finally:
            if driver:
                self._driver.close()
        return rv

    """
    """

    def getRoyaltyReport(self, group, start_date, end_date):
        royalty_data = {}
        driver = None
        try:
            self._login()
            driver = self._driver
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_header_root"].format(2)).click()
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_item_root"].format(2, 0)).click()
            driver.find_element(By.ID, "search:searchType:1").click()
            driver.find_element(By.ID, TAG_IDS["parameters_group"]).clear()
            driver.find_element(By.ID, TAG_IDS["parameters_group"]).send_keys(group)
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["start_date"]).click()
            driver.find_element(By.ID, TAG_IDS["start_date"]).clear()
            driver.find_element(By.ID, TAG_IDS["start_date"]).send_keys(
                start_date.strftime("%m%d%Y")
            )
            driver.find_element(By.ID, TAG_IDS["end_date"]).click()
            driver.find_element(By.ID, TAG_IDS["end_date"]).clear()
            driver.find_element(By.ID, TAG_IDS["end_date"]).send_keys(
                end_date.strftime("%m%d%Y")
            )
            driver.find_element(By.ID, TAG_IDS["submit"]).click()
            driver.implicitly_wait(0)
            sleep(8)
            soup = BeautifulSoup(driver.page_source, features="html.parser")
            royalty_table = soup.find("table", attrs={"id": TAG_IDS["royalty_list"]})
            if not royalty_table or not isinstance(royalty_table, Tag):
                rows = []
            else:
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
                self._driver.close()

    def toggleMealDeal(self, stores):
        driver = None
        rv = {}
        try:
            self._login()
            driver = self._driver
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_header_root"].format(1)).click()
            driver.find_element(By.ID, TAG_IDS["menu_item_root"].format(1, 8)).click()
            for store in stores:
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).clear()
                driver.find_element(By.ID, TAG_IDS["parameters_store"]).send_keys(store)
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                sleep(7)
                deal_row = driver.find_element(By.XPATH, "//input[@value='1594']")
                deal_text = deal_row.get_attribute("name").rstrip(":pluId")
                for toggle_type in ["pickup", "delivery"]:
                    driver.find_element(
                        By.ID, f"{deal_text}:availability:0:{toggle_type}"
                    ).click()
                driver.find_element(By.ID, TAG_IDS["submit"]).click()
                sleep(15)
                driver.find_element(By.ID, "parameters:continue").click()
                sleep(7)
                rv[store] = driver.find_element(
                    By.ID, f"{deal_text}:availability:0:pickup"
                ).is_selected()
        finally:
            if driver:
                self._driver.close()

        return rv

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

    Should the online amount get minused from the JM online deposit?
    No, since the online gift card entry is charged minus to online credit card   
    [ store, txdate, sold, instore, online]
    """

    def getGiftCardACH(self, stores, start_date, end_date):
        if end_date <= start_date:
            raise Exception("End date cannot be before start date.")
        driver = None
        try:
            self._login()
            driver = self._driver
            # navigate to gift card report
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_header_root"].format(0)).click()
            sleep(2)
            driver.find_element(By.ID, TAG_IDS["menu_item_root"].format(0, 10)).click()
            sleep(2)
            step_date = onDay(start_date, 4)  # always Friday
            results = []
            while step_date < end_date:
                period_end = step_date - datetime.timedelta(days=2)
                period_start = period_end - datetime.timedelta(days=6)
                for store in stores:
                    notes = str(datetime.date.today())
                    lines = []
                    search_ele = driver.find_element(By.ID, "j_id37_body")
                    if not search_ele.is_displayed():
                        driver.find_element(By.ID, "j_id37_header").click()

                    driver.find_element(By.ID, TAG_IDS["parameters_store"]).clear()
                    driver.find_element(By.ID, TAG_IDS["parameters_store"]).send_keys(
                        store
                    )
                    driver.find_element(By.ID, TAG_IDS["start_date"]).click()
                    driver.find_element(By.ID, TAG_IDS["start_date"]).clear()
                    driver.find_element(By.ID, TAG_IDS["start_date"]).send_keys(
                        period_start.strftime("%m%d%Y")
                    )
                    driver.find_element(By.ID, TAG_IDS["end_date"]).click()
                    driver.find_element(By.ID, TAG_IDS["end_date"]).clear()
                    driver.find_element(By.ID, TAG_IDS["end_date"]).send_keys(
                        period_end.strftime("%m%d%Y")
                    )

                    Select(
                        driver.find_element(By.ID, "parameters:GroupByList")
                    ).select_by_index(1)
                    driver.find_element(By.ID, TAG_IDS["submit"]).click()
                    driver.implicitly_wait(0)
                    sleep(8)
                    soup = BeautifulSoup(driver.page_source, features="html.parser")

                    giftcardsales = soup.find(
                        "table", attrs={"id": TAG_IDS["gift_card_sales"]}
                    )
                    if giftcardsales:
                        lines.append(
                            [
                                "1330",
                                "sold",
                                "-"
                                + giftcardsales.find_all("tr")[4]  # type: ignore
                                .find_all("td")[2]
                                .text.strip(),
                            ]
                        )
                    giftcardredeemed = soup.find(
                        "table", attrs={"id": TAG_IDS["gift_card_redeemed"]}
                    )

                    if giftcardredeemed:
                        lines.append(
                            [
                                "1330",
                                "instore",
                                giftcardredeemed.find_all("tr")[1]  # type: ignore
                                .find_all("td")[-3]
                                .text.strip(),
                            ]
                        )
                    if len(lines) > 0:
                        results.append(
                            [
                                "Jersey Mike's Franchise System",
                                step_date,
                                notes,
                                lines,
                                store,
                            ]
                        )
                step_date = step_date + datetime.timedelta(days=7)
            return results
        finally:
            if driver:
                self._driver.close()

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
                with open(
                    "/Users/wgreen/Google Drive/Shared drives/Wagoner Management Corp./Sales Tax/Journal/{0}-{1}_daily_journal.txt".format(
                        str(qdate), store
                    ),
                    "w",
                ) as fileout:
                    fileout.write(daily_journal[store])
            qdate = qdate - datetime.timedelta(days=1)
