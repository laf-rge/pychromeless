import logging
import os
from tempfile import mkdtemp
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Only import webdriver_manager if not running in AWS Lambda
def _get_chromedriver_service_local():
    try:
        from webdriver_manager.chrome import ChromeDriverManager

        return Service(ChromeDriverManager().install())
    except ImportError:
        raise ImportError(
            "webdriver-manager is required for local development. Please install it with 'pip install webdriver-manager'."
        )


logger = logging.getLogger(__name__)


def initialise_driver(download_location: Optional[str] = None) -> webdriver.Chrome:
    chrome_options = ChromeOptions()
    driver = None
    CHROME_HEADLESS = int(os.environ.get("CHROME_HEADLESS", "0"))
    IS_LAMBDA = "AWS_LAMBDA_FUNCTION_NAME" in os.environ
    CHROME_DEBUG_PORT = int(os.environ.get("CHROME_DEBUG_PORT", "0"))

    if IS_LAMBDA:
        # AWS Lambda: use pre-bundled binaries and explicit paths
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": (
                    download_location if download_location else "/tmp"
                ),
                "download.directory_upgrade": True,
                "download.prompt_for_download": False,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            },
        )
        if CHROME_HEADLESS == 0:
            chrome_options.add_argument("--headless=old")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--no-zygote")
        chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
        chrome_options.add_argument(f"--data-path={mkdtemp()}")
        chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        chrome_options.add_argument("--log-path=/tmp")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.binary_location = (
            "/opt/chrome/chrome-headless-shell-linux64/chrome-headless-shell"
        )
        service = Service(
            executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
            service_log_path="/tmp/chromedriver.log",
        )
        driver = webdriver.Chrome(service=service, options=chrome_options)
    elif CHROME_DEBUG_PORT:
        # Debug port mode: attach to a running Chrome instance with remote debugging enabled
        chrome_options.debugger_address = "localhost:9222"
        # Optionally set binary_location if needed
        # chrome_options.binary_location = "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        driver = webdriver.Chrome(options=chrome_options)
    else:
        # Local development: use webdriver-manager to auto-manage chromedriver
        chrome_options.binary_location = "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        chrome_options.binary_location = (
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        )
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": (
                    download_location
                    if download_location
                    else os.path.join(os.getcwd(), "downloads")
                ),
                "download.directory_upgrade": True,
                "download.prompt_for_download": False,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            },
        )
        if CHROME_HEADLESS == 0:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--no-zygote")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--window-size=1920,1080")
        # Use webdriver-manager to get the correct chromedriver
        service = _get_chromedriver_service_local()
        driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def wait_for_element(driver, locator, timeout=15) -> Optional[WebElement]:
    try:
        element = WebDriverWait(
            driver,
            timeout,
            ignored_exceptions=[
                NoSuchElementException,
                ElementNotInteractableException,
            ],
        ).until(EC.presence_of_element_located(locator))
        return element
    except TimeoutException:
        logger.warning(f"Element {locator} not found within {timeout} seconds")
        return None
