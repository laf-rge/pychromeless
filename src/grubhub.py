import datetime
import logging
import re
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
        # driver.implicitly_wait(25)

        try:
            driver.get("https://restaurant.grubhub.com/login")
        except Exception as e:
            logger.exception("Error accessing URL: %s", e)
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
            # self._driver = initialise_driver()
            # input("pause...")
            self._login()
            driver = self._driver

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
                # Get all td elements for more reliable parsing
                tds = tr.find_elements(By.TAG_NAME, "td")
                # Get date from first td element
                date_text = tds[0].text
                txdate = datetime.datetime.strptime(
                    date_text.split()[0], "%m/%d/%y"
                ).date()
                store = tds[1].text.split()[-1].strip(" ()")
                # Click the first td element for Safari compatibility
                tds[0].click()
                sleep(2)

                # Parse using HTML structure - much more reliable than text parsing!
                # Find the deposit totals container
                try:
                    totals_container = driver.find_element(
                        By.CLASS_NAME, "fin-deposit-history-deposit-totals"
                    )

                    # First line: header with main label and amount
                    header = totals_container.find_element(
                        By.CLASS_NAME, "fin-deposit-history-deposit-totals__header"
                    )
                    header_text = header.text  # e.g., "Prepaid Orders (8) $197.12"
                    # Extract label (everything before the last dollar amount)
                    amount_match = re.search(r"(\$[\d.]+)$", header_text)
                    if amount_match:
                        label = header_text[: amount_match.start()].strip()
                        amount = amount_match.group(1)
                        lines.append(["1363", label, self.convert_num(amount)])

                    # Remaining lines: terms and descriptions (skip the footer "Deposit Total")
                    definitions = totals_container.find_elements(
                        By.CLASS_NAME, "fin-deposit-history-deposit-totals__definition"
                    )
                    for definition in definitions:
                        term = definition.find_element(
                            By.CLASS_NAME, "fin-deposit-history-deposit-totals__term"
                        ).text
                        description = definition.find_element(
                            By.CLASS_NAME,
                            "fin-deposit-history-deposit-totals__description",
                        ).text
                        lines.append(["6310", term, self.convert_num(description)])

                except (NoSuchElementException, ElementNotInteractableException) as e:
                    logger.error("Could not parse deposit structure: %s", e)
                    raise

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
