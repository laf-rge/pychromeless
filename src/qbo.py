import logging
from time import sleep
from typing import Any

from selenium.webdriver.common.by import By

from webdriver import initialise_driver

logger = logging.getLogger(__name__)


driver = initialise_driver()


def fdms_reconcile() -> None:
    driver.switch_to.window(driver.window_handles[0])

    # Get the scrollable container - the div inside mainTableContainer
    table_container = driver.find_element(
        By.XPATH, "//div[@class='mainTableContainer']/div"
    )

    # Create a dictionary to store amounts and their corresponding rows
    amount_rows: dict[str, list[Any]] = {}

    # Keep track of processed rows to avoid duplicates
    processed_rows = set()

    while True:
        # Scroll down a bit
        current_height = driver.execute_script(
            "return arguments[0].scrollHeight", table_container
        )
        scroll_position = driver.execute_script(
            "return arguments[0].scrollTop", table_container
        )

        # Scroll by 1000 pixels or to the bottom if less than 1000 pixels remain
        scroll_amount = min(1000, current_height - scroll_position)
        driver.execute_script(
            f"arguments[0].scrollTop = {scroll_position + scroll_amount}",
            table_container,
        )
        sleep(1)  # Wait for new rows to load

        # Get visible rows
        rows = driver.find_elements(
            By.XPATH, "//div[@class='mainTableContainer']/div/table/tbody/tr"
        )

        # First pass - collect amounts from visible unprocessed rows
        for row in rows:
            if row.id in processed_rows:
                continue

            # Skip if checkbox is already checked
            checkbox = row.find_element(
                By.XPATH, ".//button[@data-testid='clear-state-cell']"
            )
            if checkbox.get_attribute("aria-pressed") == "true":
                processed_rows.add(row.id)
                continue

            amounts = row.find_elements(
                By.XPATH, ".//td[@class[contains(., 'numeric amount')]]"
            )
            if len(amounts) < 2:
                continue

            # Get the amount from third to last column
            amount = amounts[-2].find_element(By.TAG_NAME, "div").text.strip()
            if amount:
                if amount not in amount_rows:
                    amount_rows[amount] = []
                amount_rows[amount].append(row)

        # Second pass - find matches in visible rows
        for row in rows:
            if row.id in processed_rows:
                continue

            # Skip if checkbox is already checked
            checkbox = row.find_element(
                By.XPATH, ".//button[@data-testid='clear-state-cell']"
            )
            if checkbox.get_attribute("aria-pressed") == "true":
                processed_rows.add(row.id)
                continue
            amounts = row.find_elements(
                By.XPATH, ".//td[@class[contains(., 'numeric amount')]]"
            )
            if len(amounts) < 2:
                continue

            # Get the amount from second to last column
            amount = amounts[-1].find_element(By.TAG_NAME, "div").text.strip()
            # if the amount is 0.00, check the box and move on
            if amount == "0.00":
                checkbox = row.find_element(
                    By.XPATH, ".//button[@data-testid='clear-state-cell']"
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'})", checkbox
                )
                sleep(0.1)
                checkbox.click()
                sleep(0.1)
                processed_rows.add(row.id)
                continue

            # If this amount exists in our dictionary, we found a match
            if amount and amount in amount_rows:
                for matching_row in amount_rows[amount]:
                    # Scroll matching row into view before clicking
                    checkbox = matching_row.find_element(
                        By.XPATH, ".//button[@data-testid='clear-state-cell']"
                    )
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'})",
                        checkbox,
                    )
                    sleep(0.1)
                    checkbox.click()
                    sleep(0.1)
                    processed_rows.add(matching_row.id)

                # Scroll current row into view before clicking
                checkbox = row.find_element(
                    By.XPATH, ".//button[@data-testid='clear-state-cell']"
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'})", checkbox
                )
                sleep(0.1)
                checkbox.click()
                sleep(0.1)
                processed_rows.add(row.id)

                # Remove the processed amount to avoid duplicate matches
                del amount_rows[amount]

        # Check if we've reached the bottom
        new_scroll_position = driver.execute_script(
            "return arguments[0].scrollTop", table_container
        )
        if new_scroll_position == scroll_position:
            break
