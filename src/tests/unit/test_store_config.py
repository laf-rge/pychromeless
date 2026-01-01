import os
import sys
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from store_config import StoreConfig


class TestStoreConfig(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test fixtures with mocked SSM to avoid actual AWS calls"""
        # Mock the SSMParameterStore to raise an exception during refresh()
        with patch("store_config.SSMParameterStore") as mock_ssm_class:
            mock_ssm_instance = MagicMock()
            mock_ssm_class.return_value = mock_ssm_instance

            # Mock the __getitem__ call to raise an exception to trigger fallback
            mock_ssm_instance.__getitem__.side_effect = Exception("Mocked SSM failure")

            self.store_config = StoreConfig()

    def test_get_inventory_processing_month_january_scenarios(self) -> None:
        """Test various January scenarios where we should process December of previous year"""

        # January 1st (Monday) - should process December 2023
        result = self.store_config.get_inventory_processing_month(date(2024, 1, 1))
        self.assertEqual(result, (2023, 12))

        # January 2nd (Tuesday) - first Tuesday, should still process December 2023
        result = self.store_config.get_inventory_processing_month(date(2024, 1, 2))
        self.assertEqual(result, (2023, 12))

        # January 8th (Monday) - still before second Tuesday, should process December 2023
        result = self.store_config.get_inventory_processing_month(date(2024, 1, 8))
        self.assertEqual(result, (2023, 12))

        # January 9th (Tuesday) - second Tuesday, should process January 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 1, 9))
        self.assertEqual(result, (2024, 1))

        # January 10th (Wednesday) - after second Tuesday, should process January 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 1, 10))
        self.assertEqual(result, (2024, 1))

    def test_get_inventory_processing_month_february_scenarios(self) -> None:
        """Test February scenarios with different starting day of week"""

        # February 1st 2024 (Thursday) - should process January 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 2, 1))
        self.assertEqual(result, (2024, 1))

        # February 6th 2024 (Tuesday) - first Tuesday, should still process January 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 2, 6))
        self.assertEqual(result, (2024, 1))

        # February 13th 2024 (Tuesday) - second Tuesday, should process February 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 2, 13))
        self.assertEqual(result, (2024, 2))

        # February 14th 2024 (Wednesday) - after second Tuesday, should process February 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 2, 14))
        self.assertEqual(result, (2024, 2))

    def test_get_inventory_processing_month_march_scenarios(self) -> None:
        """Test March scenarios where first day is different"""

        # March 1st 2024 (Friday) - should process February 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 3, 1))
        self.assertEqual(result, (2024, 2))

        # March 5th 2024 (Tuesday) - first Tuesday, should still process February 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 3, 5))
        self.assertEqual(result, (2024, 2))

        # March 12th 2024 (Tuesday) - second Tuesday, should process March 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 3, 12))
        self.assertEqual(result, (2024, 3))

    def test_get_inventory_processing_month_edge_cases(self) -> None:
        """Test edge cases like leap years and months starting on Tuesday"""

        # Test a month that starts on Tuesday (May 2024 starts on Wednesday, let's use April 2024)
        # April 1st 2024 (Monday) - should process March 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 4, 1))
        self.assertEqual(result, (2024, 3))

        # April 2nd 2024 (Tuesday) - first Tuesday, should still process March 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 4, 2))
        self.assertEqual(result, (2024, 3))

        # April 9th 2024 (Tuesday) - second Tuesday, should process April 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 4, 9))
        self.assertEqual(result, (2024, 4))

        # Test February in a leap year
        # February 29th 2024 (Thursday) - should process February 2024 (after second Tuesday)
        result = self.store_config.get_inventory_processing_month(date(2024, 2, 29))
        self.assertEqual(result, (2024, 2))

    def test_get_inventory_processing_month_year_boundary(self) -> None:
        """Test December to January year boundary"""

        # December 1st 2023 - should process November 2023
        result = self.store_config.get_inventory_processing_month(date(2023, 12, 1))
        self.assertEqual(result, (2023, 11))

        # December 31st 2023 - should process December 2023 (after second Tuesday)
        result = self.store_config.get_inventory_processing_month(date(2023, 12, 31))
        self.assertEqual(result, (2023, 12))

    def test_get_inventory_processing_month_month_starting_tuesday(self) -> None:
        """Test a month that starts on Tuesday (October 2024)"""

        # October 1st 2024 (Tuesday) - first Tuesday, should process September 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 10, 1))
        self.assertEqual(result, (2024, 9))

        # October 8th 2024 (Tuesday) - second Tuesday, should process October 2024
        result = self.store_config.get_inventory_processing_month(date(2024, 10, 8))
        self.assertEqual(result, (2024, 10))


class TestStoreConfigExistingMethods(unittest.TestCase):
    """Test existing store config methods to ensure we didn't break anything"""

    def setUp(self) -> None:
        """Set up test fixtures with mocked SSM to avoid actual AWS calls"""
        # Mock the SSMParameterStore to raise an exception during refresh()
        with patch("store_config.SSMParameterStore") as mock_ssm_class:
            mock_ssm_instance = MagicMock()
            mock_ssm_class.return_value = mock_ssm_instance

            # Mock the __getitem__ call to raise an exception to trigger fallback
            mock_ssm_instance.__getitem__.side_effect = Exception("Mocked SSM failure")

            self.store_config = StoreConfig()

    def test_get_active_stores(self) -> None:
        """Test that get_active_stores works with the fallback configuration"""
        # Test with a date after both stores opened
        active_stores = self.store_config.get_active_stores(date(2024, 4, 1))
        self.assertEqual(set(active_stores), {"20400", "20407"})

        # Test with a date before store 20407 opened (March 6, 2024)
        active_stores = self.store_config.get_active_stores(date(2024, 3, 1))
        self.assertEqual(active_stores, ["20400"])

        # Test with a date before any stores opened
        active_stores = self.store_config.get_active_stores(date(2024, 1, 1))
        self.assertEqual(active_stores, [])

    def test_is_store_active(self) -> None:
        """Test is_store_active method"""
        # Test store 20400 (opened 2024-01-31)
        self.assertFalse(self.store_config.is_store_active("20400", date(2024, 1, 30)))
        self.assertTrue(self.store_config.is_store_active("20400", date(2024, 1, 31)))
        self.assertTrue(self.store_config.is_store_active("20400", date(2024, 4, 1)))

        # Test store 20407 (opened 2024-03-06)
        self.assertFalse(self.store_config.is_store_active("20407", date(2024, 3, 5)))
        self.assertTrue(self.store_config.is_store_active("20407", date(2024, 3, 6)))

        # Test non-existent store
        self.assertFalse(self.store_config.is_store_active("99999", date(2024, 4, 1)))

    def test_all_stores_property(self) -> None:
        """Test all_stores property returns sorted list"""
        all_stores = self.store_config.all_stores
        self.assertEqual(all_stores, ["20400", "20407"])


if __name__ == "__main__":
    unittest.main()
