import datetime
import json
import logging
from time import sleep
from typing import cast

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from ssm_parameter_store import SSMParameterStore
from webdriver import initialise_driver

logger = logging.getLogger(__name__)


class EZCater:
    def __init__(self):
        self._parameters = cast(
            SSMParameterStore, SSMParameterStore(prefix="/prod")["ezcater"]
        )

    def _login(self):
        self._driver = initialise_driver()
        driver = self._driver
        driver.implicitly_wait(5)
        driver.set_page_load_timeout(45)

        # logout
        # login
        try:
            driver.get("https://www.ezcater.com/caterer_portal/sign_in")
            driver.find_element(By.ID, "contact_username").send_keys(
                str(self._parameters["user"]) + Keys.ENTER
            )
            driver.find_element(By.ID, "password").send_keys(
                str(self._parameters["password"]) + Keys.ENTER
            )
            input("pause...")
        except WebDriverException as e:
            logger.exception(f"Login exception occurred: {e}")
            input("login exception...")

        WebDriverWait(driver, 45)

    def get_payments(self, stores, start_date, end_date):
        self._login()
        results = []
        driver = self._driver
        sleep(5)

        # Navigate to payments page to ensure we're in the right context
        driver.get("https://ezmanage.ezcater.com/payments")
        WebDriverWait(driver, 45)

        # GraphQL query for payments list
        list_query = {
            "operationName": "PaymentsPaymentsTablePaymentsQuery",
            "variables": {
                "direction": "DESC",  # Get newest first
                "field": "SENT_ON",
                "limit": 100,  # Increased limit to get more results at once
                "offset": 0,
            },
            "query": """
                query PaymentsPaymentsTablePaymentsQuery($offset: Int, $limit: Int, $field: VendorPaymentSortField!, $direction: SortDirection!) {
                    me {
                        catererAccount {
                            billing {
                                vendorPayments(
                                    offset: $offset
                                    limit: $limit
                                    orderBy: {field: $field, direction: $direction}
                                ) {
                                    totalCount
                                    edges {
                                        node {
                                            id
                                            sentOn
                                            name
                                            __typename
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            """,
        }

        # Execute GraphQL query for payment list
        response = driver.execute_script(
            """
            return fetch('https://ezmanage-api.ezcater.com/graphql', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': '*/*',
                },
                credentials: 'include',
                body: arguments[0]
            }).then(response => response.json());
        """,
            json.dumps([list_query]),
        )

        # Extract payment IDs and process them
        payments_data = response[0]["data"]["me"]["catererAccount"]["billing"][
            "vendorPayments"
        ]["edges"]

        for payment in payments_data:
            payment_node = payment["node"]
            payment_id = payment_node["id"]
            payment_date = datetime.datetime.strptime(
                payment_node["sentOn"], "%Y-%m-%d"
            ).date()
            store_id = payment_node["name"].split("#")[1][:5]

            if store_id in stores and start_date <= payment_date <= end_date:
                # GraphQL query for detailed payment info
                detail_query = {
                    "operationName": "PaymentDetailsPaymentsQuery",
                    "variables": {"paymentId": payment_id},
                    "query": """
                        query PaymentDetailsPaymentsQuery($paymentId: ID!) {
                            me {
                                catererAccount {
                                    billing {
                                        vendorPayment(id: $paymentId) {
                                            id
                                            sentOn
                                            name
                                            accountingTotals {
                                                food
                                                salesTax
                                                deliveryFees
                                                marketplaceCommission
                                                tips
                                                creditCardFees
                                                miscFees
                                                __typename
                                            }
                                            __typename
                                        }
                                    }
                                }
                            }
                        }
                    """,
                }

                # Execute GraphQL query for payment details
                detail_response = driver.execute_script(
                    """
                    return fetch('https://ezmanage-api.ezcater.com/graphql', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': '*/*',
                        },
                        credentials: 'include',
                        body: arguments[0]
                    }).then(response => response.json());
                """,
                    json.dumps([detail_query]),
                )

                payment_data = detail_response[0]["data"]["me"]["catererAccount"][
                    "billing"
                ]["vendorPayment"]
                result = self.extract_deposit(payment_data)
                results.extend([result])
            else:
                # logger.warning(f"skipping {store_id} {payment_date}")
                continue

        return results

    def extract_deposit(self, data):
        notes = str(data)
        lines = []
        deposit_date = datetime.datetime.strptime(data["sentOn"], "%Y-%m-%d").date()

        lines.append(["1364", "Food Total", f"{data['accountingTotals']['food']}"])
        lines.append(["2310", "Sales Tax", f"{data['accountingTotals']['salesTax']}"])
        lines.append(
            ["6310", "Delivery Fees", f"{data['accountingTotals']['deliveryFees']}"]
        )
        lines.append(
            [
                "6310",
                "Commission",
                f"-{data['accountingTotals']['marketplaceCommission']}",
            ]
        )
        lines.append(["2320", "Tips", f"{data['accountingTotals']['tips']}"])
        lines.append(
            [
                "6210",
                "Credit Card Fees",
                f"-{data['accountingTotals']['creditCardFees']}",
            ]
        )
        lines.append(
            [
                "6310",
                "ezDispatch Charges & Misc. Fees",
                f"{data['accountingTotals']['miscFees']}",
            ]
        )

        result = [
            "EZ Cater",
            deposit_date,
            notes,
            lines,
            data["name"].split("#")[1][:5],
        ]
        return result
