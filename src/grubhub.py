import csv
import datetime
import logging
import re
from decimal import Decimal
from time import sleep
from typing import Any, cast

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
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

    def __init__(self) -> None:
        self._parameters = cast(
            SSMParameterStore, SSMParameterStore(prefix="/prod")["grubhub"]
        )

    """
    """

    def _login(self) -> None:
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

    def get_payments(
        self,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ) -> list[list[Any]]:
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
                return []

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

    def convert_num(self, number: str) -> str:
        return number.replace("$", "")

    def get_payments_from_csv(
        self,
        filename: str,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ) -> list[list[Any]]:
        """Parse Grubhub deposit CSV export and return payments in same format as get_payments.

        Args:
            filename: Path to the CSV file exported from Grubhub
            start_date: Optional start date filter (datetime.date). If None, no start filter.
            end_date: Optional end date filter (datetime.date). If None, no end filter.

        Returns:
            List of payment records in format: ["Grubhub", txdate, notes, lines, store]
            where lines is a list of [account_code, description, amount] tuples
        """

        # Helper function to parse numeric values, handling "n/a" and empty strings
        def parse_decimal(value: Any) -> Decimal:
            if value in ("n/a", "", None):
                return Decimal("0")
            try:
                return Decimal(str(value))
            except (ValueError, TypeError):
                return Decimal("0")

        # Dictionary to aggregate data by deposit ID
        deposits: dict[str, dict] = {}

        try:
            with open(filename, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    deposit_id = row["Deposit ID"]

                    # Initialize deposit data if not exists
                    if deposit_id not in deposits:
                        deposits[deposit_id] = {
                            "deposit_date": None,
                            "store": None,
                            "restaurant_total": Decimal("0"),
                            "commission": Decimal("0"),
                            "delivery_commission": Decimal("0"),
                            "processing_fee": Decimal("0"),
                            "order_count": 0,
                            "adjustments": [],
                        }

                    deposit_data = deposits[deposit_id]

                    # Parse deposit date (format: 2025-11-05T12:13:42.713Z)
                    if deposit_data["deposit_date"] is None:
                        deposit_date_str = row["Deposit Date"]
                        # Extract just the date part before 'T'
                        date_part = deposit_date_str.split("T")[0]
                        deposit_data["deposit_date"] = datetime.datetime.strptime(
                            date_part, "%Y-%m-%d"
                        ).date()

                    # Extract store number from Restaurant column
                    # Format: "Jersey Mike's -  (20358)" or "Jersey Mike's - 20400"
                    if deposit_data["store"] is None:
                        restaurant = row["Restaurant"]
                        # Try to find store number in parentheses first
                        store_match = re.search(r"\((\d+)\)", restaurant)
                        if store_match:
                            deposit_data["store"] = store_match.group(1)
                        else:
                            # Fallback: extract number at the end
                            store_match = re.search(r"(\d+)$", restaurant.strip())
                            if store_match:
                                deposit_data["store"] = store_match.group(1)

                    # Aggregate totals
                    deposit_data["restaurant_total"] += parse_decimal(
                        row["Restaurant Total"]
                    )
                    deposit_data["commission"] += parse_decimal(row["Commission"])
                    deposit_data["delivery_commission"] += parse_decimal(
                        row["Delivery Commission"]
                    )
                    deposit_data["processing_fee"] += parse_decimal(
                        row["Processing Fee"]
                    )

                    # Count orders (skip adjustments)
                    if not row["Type"].startswith("Adjustment"):
                        deposit_data["order_count"] += 1

                    # Track adjustments/refunds for notes
                    if row["Type"].startswith("Adjustment"):
                        deposit_data["adjustments"].append(
                            {
                                "description": row["Description"],
                                "amount": parse_decimal(row["Restaurant Total"]),
                                "date": row["Date"],
                            }
                        )

        except FileNotFoundError:
            logger.error("CSV file not found: %s", filename)
            raise
        except Exception:
            logger.exception("Error reading CSV file: %s", filename)
            raise

        # Convert aggregated deposits to result format
        results = []
        for deposit_id, deposit_data in deposits.items():
            txdate = deposit_data["deposit_date"]
            store = deposit_data["store"]

            # Skip if missing required data
            if txdate is None or store is None:
                continue
            # Apply date filtering only if dates are specified
            if start_date is not None and txdate < start_date:
                continue
            if end_date is not None and txdate > end_date:
                continue

            # Build notes from adjustments
            notes = ""
            if deposit_data["adjustments"]:
                adjustment_texts = []
                for adj in deposit_data["adjustments"]:
                    adjustment_texts.append(
                        f"{adj['date']}: {adj['description']} ${adj['amount']}"
                    )
                notes = "Refunds/Adjustments:\n" + "\n".join(adjustment_texts)

            # Build lines array matching get_payments format
            lines = []

            # First line: main deposit total (account 1363 = Grubhub)
            order_count = deposit_data["order_count"]
            main_label = f"Prepaid Orders ({order_count})"
            main_amount = deposit_data["restaurant_total"]
            lines.append(
                ["1363", main_label, str(main_amount.quantize(Decimal("0.01")))]
            )

            # Additional lines for deductions (account 6310 = Other Current Assets)
            # Preserve negative signs as they represent deductions
            if deposit_data["commission"] != 0:
                lines.append(
                    [
                        "6310",
                        "Commission",
                        str(deposit_data["commission"].quantize(Decimal("0.01"))),
                    ]
                )

            if deposit_data["delivery_commission"] != 0:
                lines.append(
                    [
                        "6310",
                        "Delivery Commission",
                        str(
                            deposit_data["delivery_commission"].quantize(
                                Decimal("0.01")
                            )
                        ),
                    ]
                )

            if deposit_data["processing_fee"] != 0:
                lines.append(
                    [
                        "6310",
                        "Processing Fee",
                        str(deposit_data["processing_fee"].quantize(Decimal("0.01"))),
                    ]
                )

            results.append(["Grubhub", txdate, notes, lines, store])

        return results
