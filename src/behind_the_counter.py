import os
import time
from typing import cast

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ssm_parameter_store import SSMParameterStore


class BehindTheCounter:
    def __init__(self) -> None:
        self.url = "https://franchisee.jerseymikes.com/"
        self._parameters = cast(
            dict[str, str], SSMParameterStore(prefix="/prod")["btc"]
        )
        self.username = str(self._parameters["user"])
        self.password = str(self._parameters["password"])
        self.driver: webdriver.Chrome | None = None
        self.store_id = "20407"  # Store ID from the export URL

    def setup_driver(self) -> None:
        """Setup Chrome driver with necessary options"""
        chrome_options = webdriver.ChromeOptions()
        # Add options for headless mode if needed
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Set up download directory
        download_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(download_dir, exist_ok=True)
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)

    def login(self) -> bool:
        """Login to the website"""
        if not self.driver:
            raise RuntimeError("Driver not initialized. Call setup_driver() first.")

        try:
            self.driver.get(self.url)

            # Wait for login form elements using the provided HTML structure
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")

            # Fill in credentials
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)

            # Find and click login button using the provided HTML
            login_button = self.driver.find_element(By.ID, "submit-button")
            login_button.click()

            # Wait for successful login by checking if we're redirected
            WebDriverWait(self.driver, 10).until(
                lambda driver: "log-in-out.php" not in driver.current_url
            )
            return True

        except TimeoutException:
            print("Login failed - timeout waiting for elements")
            return False
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def download_csv(self) -> bool:
        """Navigate to export page and download CSV"""
        if not self.driver:
            raise RuntimeError("Driver not initialized. Call setup_driver() first.")

        try:
            # Direct navigation to the export URL
            export_url = f"https://franchisee.jerseymikes.com/price-change-perm/export.php?stores={self.store_id}&action=export"
            self.driver.get(export_url)

            # Wait for download to complete by checking the download directory
            download_dir = os.path.join(os.getcwd(), "downloads")
            timeout = time.time() + 30  # 30 second timeout

            while time.time() < timeout:
                files = os.listdir(download_dir)
                csv_files = [
                    f
                    for f in files
                    if f.endswith(".csv") and not f.endswith(".crdownload")
                ]
                if csv_files:
                    print(f"Download completed: {csv_files[-1]}")
                    return True
                time.sleep(1)

            raise TimeoutException("CSV download did not complete within 30 seconds")

        except Exception as e:
            print(f"CSV download failed: {str(e)}")
            return False

    def cleanup(self) -> None:
        """Close the browser and cleanup"""
        if self.driver:
            self.driver.quit()
