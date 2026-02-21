import csv
import datetime
import glob
import io
import json
import logging
import os
import re
import zipfile
from time import sleep
from typing import Any, cast

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ssm_parameter_store import SSMParameterStore
from webdriver import initialise_driver

logger = logging.getLogger(__name__)

store_map = {
    "20358": "23026026",
    "20395": "24923975",
    "20400": "26026815",
    "20407": "27848178",
}

store_inv_map = {v: k for k, v in store_map.items()}

COMPANY_ID = "1431"


class Doordash:
    """"""

    def __init__(self) -> None:
        self._parameters = cast(
            SSMParameterStore, SSMParameterStore(prefix="/prod")["doordash"]
        )
        self._driver = initialise_driver()

    def _login(self) -> None:
        self._driver = initialise_driver()
        driver = self._driver
        driver.implicitly_wait(25)
        driver.set_page_load_timeout(45)

        driver.get("https://merchant-portal.doordash.com/merchant/logout")
        driver.get("https://merchant-portal.doordash.com/")
        driver.find_element(
            By.XPATH, '//input[@data-anchor-id="IdentityLoginPageEmailField"]'
        ).send_keys(str(self._parameters["user"]) + Keys.ENTER)
        driver.find_element(
            By.XPATH, '//input[@data-anchor-id="IdentityLoginPagePasswordField"]'
        ).send_keys(str(self._parameters["password"]))
        driver.find_element(By.ID, "login-submit-button").click()
        input("pause...")

    def get_payments(
        self,
        _stores: list[str],
        _start_date: datetime.date,
        _end_date: datetime.date,
    ) -> list[list[Any]]:
        self._login()
        driver = self._driver

        results: list[list[Any]] = []

        driver.get(
            f"https://merchant-portal.doordash.com/merchant/financials?business_id={COMPANY_ID}"
        )

        driver.find_element(
            By.XPATH, '//button[@data-anchor-id="TimeFrameSelector"]'
        ).click()
        sleep(1)
        # driver.find_element(By.XPATH,
        #        '//label[normalize-space()="Last 30 Days"]/../..'
        #        ).find_element(By.TAG_NAME, 'input').click()
        # sleep(1)
        driver.find_element(By.XPATH, '//button[normalize-space()="Apply"]').click()
        sleep(2)

        payout_ids = []
        for tr in driver.find_elements(By.TAG_NAME, "tr")[1:]:
            cells = tr.find_elements(By.TAG_NAME, "td")
            payout_id = cells[1].text
            matches = re.search(r"\((\d+)\)", cells[3].text)
            store_id = matches.group(1) if matches else "20025"
            if store_id == "20025":
                continue
            payout_ids.append(
                f"https://merchant-portal.doordash.com/merchant/financials/payout-details/{COMPANY_ID}/{store_map[store_id]}/{payout_id}"
            )

        for payout_id in payout_ids:
            payment = self._extract_payment(payout_id)
            if payment is not None:
                results.append(payment)
        return results

    def _extract_payment(self, payout_id: str) -> list | None:
        """
        Extract payment details from a DoorDash payout page.

        Args:
            payout_id (str): The payout URL to extract details from.

        Returns:
            list | None: The extracted payment details, or None if store is not found.
        """
        driver = self._driver
        lines = []
        driver.get(f"{payout_id}?business_id={COMPANY_ID}")
        sleep(3)

        txdate_str = driver.find_element(
            By.XPATH, "//*[contains(text(),'Payout on')]"
        ).text
        logger.info("txdate_str: %s", txdate_str)
        txdate = datetime.datetime.strptime(txdate_str, "Payout on %B %d, %Y").date()

        # Click the 'Show details' button
        driver.find_element(By.XPATH, "//button[.//span[text()='Show details']]").click()
        sleep(1)

        notes = {}
        # Extract all amounts by finding label spans and their next sibling value spans
        labels = [
            "Subtotal",
            "Tax (subtotal)",
            "Customer fees",
            "Tax (customer fees)",
            "Commission",
            "Merchant fees",
            "Tax (merchant fees)",
            "Error charges",
            "Adjustments",
            "Marketing fees",
            "Customer discounts",
            "Marketing credit",
            "Third-party contribution",
        ]

        # Temporarily reduce timeout for data extraction since page is already loaded
        original_implicit_wait = driver.timeouts.implicit_wait
        driver.implicitly_wait(
            2
        )  # 2 seconds should be plenty for already-loaded elements

        try:
            for label in labels:
                try:
                    label_span = driver.find_element(
                        By.XPATH, f"//span[normalize-space(text())='{label}']"
                    )
                    # Navigate up to the parent div, then find the sibling div containing the value
                    value_span = (
                        label_span.find_element(
                            By.XPATH,
                            "../following-sibling::div[1]//span",
                        )
                        if label != "Customer discounts"
                        else label_span.find_element(
                            By.XPATH,
                            "../../following-sibling::span",
                        )
                    )
                    value = value_span.text.strip().replace("$", "").replace(",", "")
                    if value:
                        notes[label] = value
                except Exception:
                    logger.warning("Error extracting %s", label)
                    continue  # Label not found, skip
        finally:
            # Restore original timeout
            driver.implicitly_wait(original_implicit_wait)
        logger.info("notes: %s", notes)
        if "Subtotal" in notes:
            lines.append(["1361", "Subtotal", notes["Subtotal"]])
        if "Tax (subtotal)" in notes:
            lines.append(["1361", "Tax", notes["Tax (subtotal)"]])
        if "Commission" in notes:
            lines.append(["6310", "Commission", notes["Commission"]])
        if "Merchant fees" in notes:
            lines.append(["6310", "Merchant fees", notes["Merchant fees"]])
        if "Marketing fees" in notes:
            lines.append(
                [
                    "6101",
                    "Marketing fees",
                    notes["Marketing fees"],
                ]
            )
        if "Marketing credit" in notes:
            lines.append(
                [
                    "6101",
                    "Marketing credit",
                    notes["Marketing credit"],
                ]
            )
        if "Third-party contribution" in notes:
            lines.append(
                [
                    "6101",
                    "Third-party contribution",
                    notes["Third-party contribution"],
                ]
            )
        if "Customer discounts" in notes:
            lines.append(
                [
                    "6101",
                    "Customer discounts",
                    notes["Customer discounts"],
                ]
            )
        if "Error charges" in notes:
            lines.append(["4830", "Error charges", notes["Error charges"]])
        if "Adjustments" in notes:
            lines.append(["4830", "Adjustments", notes["Adjustments"]])
        # tips, merchant fee tax and customer fees tax not implemented
        store = store_inv_map.get(payout_id.split("/")[7], None)
        if store is None:
            return None
        return [
            "Doordash",
            txdate,
            str(notes),
            lines,
            store,
        ]

    def _process_payments(
        self, start_date: datetime.date, end_date: datetime.date
    ) -> list[list[Any]]:
        filename = glob.glob("/tmp/summary*.zip")[0]
        results: list[list[Any]] = []
        with zipfile.ZipFile(filename) as z:
            directory = z.infolist()
            if len(directory) == 0:
                logger.warning("No results in this time frame for Doordash")
                return results
            with io.TextIOWrapper(z.open(directory[0]), encoding="utf-8") as f:
                p_reader = csv.reader(f)

                header = None

                for row in p_reader:
                    if header:
                        notes = json.dumps(dict(zip(header, row)))
                        lines = []
                        lines.append(
                            ["1361", "SUBTOTAL", row[header.index("SUBTOTAL")]]
                        )
                        lines.append(
                            ["1361", "TAX_SUBTOTAL", row[header.index("TAX_SUBTOTAL")]]
                        )
                        lines.append(
                            [
                                "6310",
                                "COMMISSION",
                                "-" + row[header.index("COMMISSION")],
                            ]
                        )
                        lines.append(
                            [
                                "4830",
                                "error charges",
                                "-" + row[header.index("error charges")],
                            ]
                        )
                        lines.append(
                            [
                                "4830",
                                "adjustments",
                                # are these positive? "-" +
                                row[header.index("adjustments")],
                            ]
                        )
                        txdate = datetime.datetime.strptime(
                            row[header.index("PAYOUT_DATE")], "%Y-%m-%d"
                        ).date()
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
