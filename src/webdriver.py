import logging
import os
from tempfile import mkdtemp
from typing import Optional, Union

from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    SessionNotCreatedException,
    TimeoutException,
    WebDriverException,
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
    except ImportError as exc:
        raise ImportError(
            "webdriver-manager is required for local development. Please install it with 'pip install webdriver-manager'."
        ) from exc


logger = logging.getLogger(__name__)

# Global Safari driver instance (Safari only allows one active session)
_safari_driver: Optional[webdriver.Safari] = None


def initialise_driver(
    download_location: Optional[str] = None,
) -> Union[webdriver.Chrome, webdriver.Safari]:

    chrome_options = ChromeOptions()
    driver = None
    CHROME_HEADLESS = int(os.environ.get("CHROME_HEADLESS", "0"))
    IS_LAMBDA = "AWS_LAMBDA_FUNCTION_NAME" in os.environ
    CHROME_DEBUG_PORT = int(os.environ.get("CHROME_DEBUG_PORT", "0"))
    USE_SAFARI = int(os.environ.get("USE_SAFARI", "0"))

    # Safari mode for local development - reuse singleton instance
    if USE_SAFARI:
        global _safari_driver

        # Check if existing driver is still valid
        if _safari_driver is not None:
            try:
                # Try to access a property to verify the session is still active
                _ = _safari_driver.current_url
                logger.debug("Reusing existing Safari WebDriver session")
                return _safari_driver
            except (WebDriverException, AttributeError):
                # Session is stale, clean it up
                logger.warning("Existing Safari session is stale, cleaning up")
                try:
                    _safari_driver.quit()
                except (WebDriverException, AttributeError):
                    pass
                _safari_driver = None

        # Create new Safari driver, handling "already paired" error
        try:
            _safari_driver = webdriver.Safari()
            logger.debug("Created new Safari WebDriver session")
            return _safari_driver
        except SessionNotCreatedException as e:
            if "already paired" in str(e).lower():
                logger.warning(
                    "Safari is already paired with another WebDriver session. "
                    "Please close any existing Safari windows and try again."
                )
                # Try to clean up and create again
                _safari_driver = None
                raise RuntimeError(
                    "Safari WebDriver session conflict. Please close all Safari windows "
                    "and any existing WebDriver sessions, then try again."
                ) from e
            raise

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
    elif CHROME_DEBUG_PORT != 0:
        # Debug port mode: attach to a running Chrome instance with remote debugging enabled
        chrome_options.debugger_address = "localhost:9222"
        # Optionally set binary_location if needed
        # chrome_options.binary_location = "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        driver = webdriver.Chrome(options=chrome_options)
    else:
        # Local development: use webdriver-manager to auto-manage chromedriver
        chrome_options.binary_location = "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
        # chrome_options.binary_location = (
        #    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        # )
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


def cleanup_safari_driver() -> None:
    """
    Clean up the global Safari WebDriver instance.

    This is useful for recovering from "already paired" errors or when you want
    to ensure a fresh Safari session. Call this before creating a new driver
    if you encounter session conflicts.
    """
    global _safari_driver
    if _safari_driver is not None:
        try:
            _safari_driver.quit()
            logger.debug("Cleaned up Safari WebDriver session")
        except (WebDriverException, AttributeError):
            logger.debug("Safari driver was already closed or invalid")
        finally:
            _safari_driver = None


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
