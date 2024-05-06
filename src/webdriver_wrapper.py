import os
import shutil
import uuid
from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.common.by import By

class WebDriverWrapper:
    def __init__(self, download_location=None):
        in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        options = webdriver.ChromeOptions()
        service = webdriver.ChromeService("/opt/chromedriver")
        
        if in_aws:
            options.binary_location = '/opt/chrome/chrome'
            options.add_argument("--headless=new")
        else:
            options.binary_location = '/opt/chrome/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,900")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument("--no-first-run")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--hide-scrollbars")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--enable-logging")
        options.add_argument("--log-level=0")
        options.add_argument("--v=99")
        options.add_argument("--password-store=basic")
        options.add_argument("--disable-extensions")
        options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
        options.add_argument("--dns-prefetch-disable")
        options.add_argument(
                "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.3163.100 Safari/537.36"
            )
        options.add_experimental_option("prefs", {"download.default_directory": download_location if download_location else "/tmp",
            "download.directory_upgrade": True, "download.prompt_for_download": False,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False})
        self.download_location=download_location
        
        self._driver = webdriver.Chrome(options=options, service=service)

    def close(self):
        # Close webdriver connection
        if self._driver:
            self._driver.quit()
        self._driver=None

        # TODO: cleanup temp directories from mkdtemp

        # Remove possible core dumps
        folder = "/tmp"
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if (
                    "core.headless-chromi" in file_path
                    and os.path.exists(file_path)
                    and os.path.isfile(file_path)
                ):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

class WebDriverWrapperOld:
    def __init__(self, download_location=None):
        in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        chrome_options = webdriver.ChromeOptions()
        self._tmp_folder = "/tmp/{}".format(uuid.uuid4())
        self.download_location = download_location

        if not os.path.exists(self._tmp_folder):
            os.makedirs(self._tmp_folder)

        if not os.path.exists(self._tmp_folder + "/user-data"):
            os.makedirs(self._tmp_folder + "/user-data")

        if not os.path.exists(self._tmp_folder + "/data-path"):
            os.makedirs(self._tmp_folder + "/data-path")

        if not os.path.exists(self._tmp_folder + "/cache-dir"):
            os.makedirs(self._tmp_folder + "/cache-dir")

        if self.download_location:
            prefs = {
                "download.default_directory": download_location,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "safebrowsing.disable_download_protection": True,
                "profile.default_content_setting_values.automatic_downloads": 1,
            }

            if in_aws:
                chrome_options.add_experimental_option("prefs", prefs)

        if in_aws:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1280x1696")
            chrome_options.add_argument(
                "--user-data-dir={}".format(self._tmp_folder + "/user-data")
            )
            chrome_options.add_argument("--hide-scrollbars")
            chrome_options.add_argument("--enable-logging")
            chrome_options.add_argument("--log-level=0")
            chrome_options.add_argument("--v=99")
            chrome_options.add_argument("--single-process")
            chrome_options.add_argument(
                "--data-path={}".format(self._tmp_folder + "/data-path")
            )
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--homedir={}".format(self._tmp_folder))
            chrome_options.add_argument(
                "--disk-cache-dir={}".format(self._tmp_folder + "/cache-dir")
            )
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
            )

            chrome_options.binary_location = "/opt/bin/headless-chromium"
        else:
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        self._driver = webdriver.Chrome(chrome_options=chrome_options)

        if self.download_location:
            self.enable_download_in_headless_chrome()

    def get_url(self, url):
        self._driver.get(url)

    def set_input_value(self, xpath, value):
        elem_send = self._driver.find_element(By.XPATH, xpath)
        elem_send.send_keys(value)

    def click(self, xpath):
        elem_click = self._driver.find_element(By.XPATH, xpath)
        elem_click.click()

    def get_inner_html(self, xpath):
        elem_value = self._driver.find_element(By.XPATH, xpath)
        return elem_value.get_attribute("innerHTML")

    def find(self, xpath):
        return self._driver.find_element(By.XPATH, xpath)

    def close(self):
        # Close webdriver connection
        self._driver.quit()

        # Remove specific tmp dir of this "run"
        shutil.rmtree(self._tmp_folder)

        # Remove possible core dumps
        folder = "/tmp"
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if (
                    "core.headless-chromi" in file_path
                    and os.path.exists(file_path)
                    and os.path.isfile(file_path)
                ):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

    def enable_download_in_headless_chrome(self):
        """
        This function was pulled from
        https://github.com/shawnbutton/PythonHeadlessChrome/blob/master/driver_builder.py#L44

        There is currently a "feature" in chrome where
        headless does not allow file download: https://bugs.chromium.org/p/chromium/issues/detail?id=696481

        Specifically this comment ( https://bugs.chromium.org/p/chromium/issues/detail?id=696481#c157 )
        saved the day by highlighting that download wasn't working because it was opening up in another tab.

        This method is a hacky work-around until the official chromedriver support for this.
        Requires chrome version 62.0.3196.0 or above.
        """
        self._driver.execute_script(
            "var x = document.getElementsByTagName('a'); var i; for (i = 0; i < x.length; i++) { x[i].target = '_self'; }"
        )
        # add missing support for chrome "send_command"  to selenium webdriver
        self._driver.command_executor._commands["send_command"] = (
            "POST",
            "/session/$sessionId/chromium/send_command",
        )

        params = {
            "cmd": "Page.setDownloadBehavior",
            "params": {"behavior": "allow", "downloadPath": self.download_location},
        }
        command_result = self._driver.execute("send_command", params)
        print("response from browser:")
        for key in command_result:
            print("result:" + key + ":" + str(command_result[key]))
