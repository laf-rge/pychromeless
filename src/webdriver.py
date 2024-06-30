import logging
import os
from tempfile import mkdtemp
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def initialise_driver(download_location: Optional[str] = None) -> webdriver.Chrome:
    chrome_options = ChromeOptions()
    driver = None
    CHROME_HEADLESS = int(os.environ.get("CHROME_HEADLESS", "0"))
    if CHROME_HEADLESS > 1:
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script(
            "var x = document.getElementsByTagName('a'); var i; for (i = 0; i < x.length; i++) { x[i].target = '_self'; }"
        )
        # add missing support for chrome "send_command"  to selenium webdriver
        driver.command_executor._commands["send_command"] = (  # type: ignore hack for lambda
            "POST",
            "/session/$sessionId/chromium/send_command",
        )

        params = {
            "cmd": "Page.setDownloadBehavior",
            "params": {"behavior": "allow", "downloadPath": download_location},
        }
        command_result = driver.execute("send_command", params)
        print("response from browser:")
        for key in command_result:
            print("result:" + key + ":" + str(command_result[key]))
    else:
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": download_location
                if download_location
                else "/tmp",
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
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
        chrome_options.add_argument(f"--data-path={mkdtemp()}")
        chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        chrome_options.add_argument("--remote-debugging-pipe")
        chrome_options.add_argument("--verbose")
        chrome_options.add_argument("--log-path=/tmp")
        chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"
        service = Service(
            executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
            service_log_path="/tmp/chromedriver.log",
        )
        driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver
