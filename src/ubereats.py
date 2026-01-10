import calendar
import datetime
import logging
from time import sleep
from typing import Any, cast

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ssm_parameter_store import SSMParameterStore
from store_config import StoreConfig
from webdriver import initialise_driver

logger = logging.getLogger(__name__)


class UberEats:
    """"""

    def __init__(self, store_config: StoreConfig):
        self._store_config = store_config
        self._parameters = cast(
            SSMParameterStore, SSMParameterStore(prefix="/prod")["ubereats"]
        )
        self._month_abbr_to_num = {
            name: num for num, name in enumerate(calendar.month_abbr) if num
        }
        self._month_to_num = {
            name: num for num, name in enumerate(calendar.month_name) if num
        }
        self._day_endings = {
            1: "st",
            2: "nd",
            3: "rd",
            21: "st",
            22: "nd",
            23: "rd",
            31: "st",
        }
        self._driver: Any = None

    """
    """

    def _login(self) -> None:
        self._driver = initialise_driver()
        driver = self._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get("https://restaurant.uber.com/manager/logout")
        sleep(5)
        driver.get("https://restaurant.uber.com/")
        driver.find_element(By.ID, "PHONE_NUMBER_or_EMAIL_ADDRESS").send_keys(
            str(self._parameters["user"]) + Keys.RETURN
        )
        sleep(3)
        # driver.find_element(By.ID, "PASSWORD").send_keys(
        #    self._parameters["password"] + Keys.RETURN
        # )
        sleep(2)
        # for element, pin in zip(
        #     driver.find_elements(By.XPATH, "//input"), self._parameters["pin"]
        # ):
        #     element.send_keys(pin)
        # driver.find_element(By.XPATH, "//button").click()
        # sleep(10)
        input("pause...")

    def __get_month_year(self) -> tuple[int, int]:
        if not self._driver:
            raise RuntimeError("Driver not initialized")
        driver = self._driver
        sleep(2)
        month = driver.find_element(
            By.XPATH, '//button[@aria-label="Previous month."]/following-sibling::*'
        ).text
        logger.info(month)
        year = driver.find_element(
            By.XPATH,
            '//button[@aria-label="Previous month."]/following-sibling::*/following-sibling::*',
        ).text
        month = self._month_to_num[month]
        year = int(year)
        return month, year

    def _click_date(self, qdate: datetime.date) -> None:
        if not self._driver:
            raise RuntimeError("Driver not initialized")
        driver = self._driver
        ActionChains(driver).send_keys(Keys.RETURN).perform()
        start_date = (
            driver.find_element(By.XPATH, '//input[@aria-label="Select a date range."]')
            .get_attribute("value")
            .split()[0]
        )
        driver.find_element(By.XPATH, '//input[@aria-label="Select a date range."]')
        while start_date != str(qdate).replace("-", "/"):
            date_text = qdate.strftime(
                "%A, %B %-d{} %Y. It's available.".format(
                    self._day_endings.get(qdate.day, "th")
                )
            )

            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            sleep(2)

            driver.find_element(
                By.XPATH, '//input[@aria-label="Select a date range."]'
            ).click()

            while True:
                try:
                    year = self.__get_month_year()[1]
                    break
                except Exception as ex:
                    logger.exception("get year failed")
                    raise ex
            while year != qdate.year:
                if year > qdate.year:
                    logger.info("moving back a month - year search")
                    driver.find_element(
                        By.XPATH, '//button[@aria-label="Previous month."]'
                    ).click()
                elif year < qdate.year:
                    logger.info("moving forward a month - year search")
                    driver.find_element(
                        By.XPATH, '//button[@aria-label="Next month."]'
                    ).click()
                else:
                    break
                year = self.__get_month_year()[1]
            month = self.__get_month_year()[0]
            try:
                while month != qdate.month:
                    if month > qdate.month:
                        logger.info("going back a month - month search")
                        driver.find_element(
                            By.XPATH, '//button[@aria-label="Previous month."]'
                        ).click()
                    else:
                        logger.info("going forward a month - month search")
                        driver.find_element(
                            By.XPATH, '//button[@aria-label="Next month."]'
                        ).click()
                    month = self.__get_month_year()[0]
            except Exception as ex:
                logger.exception("month search failed trying anyway")
                raise ex
            sleep(2)
            logger.info('//div[contains(@aria-label, "{}")]'.format(date_text))
            driver.find_element(
                By.XPATH, '//div[contains(@aria-label, "{}")]'.format(date_text)
            ).click()
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            return
        return

    def get_payments(
        self,
        stores: list[str],
        start_date: datetime.date | None,
        end_date: datetime.date | None,
    ) -> list[list[Any]]:
        if start_date is None:
            start_date = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday() + 14)
            )
            end_date = datetime.date.today()
        if end_date is None:
            end_date = datetime.date.today()
        end_date = end_date - datetime.timedelta(days=end_date.weekday())
        results = []
        for store in stores:
            qdate = start_date

            try:
                while qdate < end_date:
                    logger.info("Week of {}".format(qdate))
                    if not self._store_config.is_store_active(store, qdate):
                        logger.warn(f"skipping {store} {qdate} - not in date range")
                    else:
                        results.extend([self.get_payment(store, qdate)])
                    qdate = qdate + datetime.timedelta(days=7)
            finally:
                # self._driver._driver.close()
                pass
        return results

    def extract_deposit(
        self, driver: Any, store: str, qdate: datetime.date
    ) -> list[Any]:
        notes = ""
        lines = []
        # see what dates we are examining
        report_start, report_end = (
            driver.find_element(By.XPATH, '//input[@aria-label="Select a date range."]')
            .get_attribute("value")
            .split("–")
        )
        # earnings
        earnings = driver.find_element(By.XPATH, '//li[@tabindex="-1"]')
        lis = earnings.find_element(By.XPATH, "..").find_elements(By.TAG_NAME, "li")
        lis[-2].click()
        lis[0].click()
        earnings.click()

        txt = earnings.find_element(By.XPATH, "..").text.split("\n")
        # print(txt)
        invoice = {txt[i]: self.convert_num(txt[i + 1]) for i in range(0, len(txt), 2)}
        # print(invoice)

        # third party
        lines.append(["1362", "Sales", invoice["Sales (excl. tax)"]])

        # tips
        if "Customer contributions" in invoice:
            lines.append(
                ["2320", "Customer contributions", invoice["Customer contributions"]]
            )
        if "Customer Refunds" in invoice:
            lines.append(["4830", "Customer Refunds", invoice["Customer Refunds"]])
        if "Net Order Error Adjustments" in invoice:
            lines.append(
                [
                    "4830",
                    "Net Order Error Adjustments",
                    invoice["Net Order Error Adjustments"],
                ]
            )
        if "Marketing" in invoice:
            lines.append(["1362", "Uber Marketing", invoice["Marketing"]])
        if "Other payments" in invoice:
            lines.append(["6310", "Other payments", invoice["Other payments"]])
        # if 'Marketplace Facilitator (MF) Tax' in invoice:
        #    lines.append(["2310", 'Marketplace Facilitator Tax', invoice['Marketplace Facilitator (MF) Tax']])
        # if 'Total Taxes' in invoice:
        #    lines.append(["1361", 'Total Taxes', invoice['Total Taxes']])
        lines.append(["6310", "Uber Fees", invoice["Uber Fees"]])
        notes += str(txt)

        # pay day is always Monday
        result = [
            "Uber Eats",
            qdate - datetime.timedelta(days=(qdate.weekday() - 8)),
            notes,
            lines,
            store,
        ]
        logger.info(
            "Complete",
            extra={
                "report_start": report_start,
                "report_end": report_end,
                "qdate": qdate.isoformat(),
                "result": result,
            },
        )
        return result

    def get_payment(self, store: str, qdate: datetime.date | None = None) -> list[Any]:
        if isinstance(qdate, type(None)):
            qdate = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday() + 7)
            )
        else:
            qdate = qdate - datetime.timedelta(days=(qdate.weekday()))
        if not self._store_config.is_store_active(store, qdate):
            qdate = self._store_config.get_store_open_date(store)
        if not self._driver:
            self._login()
        if not self._driver:
            raise RuntimeError("Driver not initialized")
        driver = self._driver
        driver.get(
            "https://restaurant.uber.com/v2/payments?restaurantUUID={}".format(
                self._store_config.get_store_ubereats_uuid(store)
            )
        )
        logger.info("Getting payments for {}".format(qdate))

        qdate2 = qdate - datetime.timedelta(days=(qdate.weekday() + 7))
        if not self._store_config.is_store_active(store, qdate2):
            qdate2 = self._store_config.get_store_open_date(store)
        sleep(3)
        self._click_date(qdate2)
        sleep(3)
        self._click_date(qdate)
        sleep(3)

        result = self.extract_deposit(driver, store, qdate)
        return result

    def convert_num(self, number: str) -> str:
        if ")" in number:
            return "-" + number[2:-1]
        else:
            return number.replace("$", "")
