import datetime
import logging
from time import sleep
from typing import cast

from selenium.common.exceptions import (
    ElementNotInteractableException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ssm_parameter_store import SSMParameterStore
from webdriver import initialise_driver

logger = logging.getLogger(__name__)


class Grubhub:
    """"""

    def __init__(self):
        self._parameters = cast(
            SSMParameterStore, SSMParameterStore(prefix="/prod")["grubhub"]
        )

    """
    """

    def _login(self):
        self._driver = initialise_driver()
        driver = self._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get("https://restaurant.grubhub.com/financials/deposit-history/1669366/")
        sleep(3)
        driver.find_elements(By.XPATH, "//input")[0].send_keys(
            str(self._parameters["user"])
        )
        sleep(4)
        driver.find_elements(By.XPATH, "//input")[1].send_keys(
            str(self._parameters["password"]) + Keys.ENTER
        )
        sleep(4)
        return

    def get_payments(self, start_date=None, end_date=None):
        if isinstance(start_date, type(None)):
            start_date = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday() + 7)
            )
        if isinstance(end_date, type(None)):
            end_date = datetime.date.today() - datetime.timedelta(
                days=(datetime.date.today().weekday() - 7)
            )

        driver = None
        try:
            self._driver = initialise_driver()
            input("pause...")
            driver = self._driver

            # First switch to the first window to ensure we're in a valid context
            driver.switch_to.window(driver.window_handles[0])

            # Then look for the Grubhub tab
            grubhub_handle = None
            for handle in driver.window_handles:
                driver.switch_to.window(handle)
                if "Grubhub" in driver.title:
                    grubhub_handle = handle
                    break

            if not grubhub_handle:
                logger.warning("Could not find Grubhub tab")
                raise Exception("Could not find Grubhub tab")

            try:
                driver.get(
                    "https://restaurant.grubhub.com/financials/deposit-history/3192172,6177240,7583896,7585040/"
                )
            except Exception as e:
                logger.warning(f"Error accessing URL: {str(e)}")
                raise

            sleep(2)
            driver.find_element(By.CLASS_NAME, "date-picker-input__date-button").click()
            driver.find_element(By.LINK_TEXT, "Last 30 days").click()

            sleep(10)
            try:
                driver.find_element(
                    By.CLASS_NAME, "date-picker-input__date-button"
                ).click()
                driver.find_element(By.LINK_TEXT, "Last 30 days").click()
            except (ElementNotInteractableException, TimeoutException):
                logger.warning("Payment period dropdowns not found on page.")
            except WebDriverException as e:
                logger.exception(f"WebDriver error during payment scraping: {e}")
                return

            sleep(15)

            results = []

            for tr in driver.find_elements(By.CLASS_NAME, "fin-deposits-table-row"):
                notes = ""
                lines = []
                txdate = datetime.datetime.strptime(
                    tr.text.split()[0], "%m/%d/%y"
                ).date()
                store = tr.text.split()[4].strip(" ()")
                tr.click()
                sleep(2)
                txt = (
                    driver.find_element(
                        By.XPATH,
                        '//div[@class="fin-deposit-history-deposit-details__section fin-deposit-history-deposit-details__section--bleed"]',
                    )
                    .text.replace(")", ")\n")
                    .replace("Total", "Total\n")
                    .split("\n")
                )
                logger.info(txt, extra={"txdate": txdate.isoformat(), "store": store})

                for i in range(0, len(txt), 2):
                    if i == 0:
                        lines.append(["1363", txt[0], self.convert_num(txt[1])])
                    elif i == len(txt) - 2:
                        continue  # skip the deposit total
                    else:
                        lines.append(["6310", txt[i], self.convert_num(txt[i + 1])])

                refunds = driver.find_elements(By.XPATH, "//h5")[0]
                if refunds.text.split()[0] == "Refunds":
                    # lines.append(['4830',txt[i],self.convert_num(txt[i+1])])
                    notes += str(
                        refunds.find_element(By.XPATH, "following-sibling::*").text
                    )
                    # this is hard so skip it
                    pass

                if start_date <= txdate and txdate <= end_date:
                    results.append(["Grubhub", txdate, notes, lines, store])
                driver.find_element(
                    By.XPATH,
                    '//div[@class="transactions-order-details-header__info-bar__close"]',
                ).click()
            return results

        except Exception as e:
            logger.exception("Error in get_payments")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            raise e

    def convert_num(self, number):
        return number.replace("$", "")
