import json
import logging
from datetime import date
from typing import cast

from botocore.exceptions import ClientError

from ssm_parameter_store import SSMParameterStore

logger = logging.getLogger(__name__)


class StoreConfig:
    def __init__(self, prefix: str = "/prod"):
        self._store_config: dict = {}
        self._ssm = SSMParameterStore(prefix=prefix)
        self.refresh()

    def refresh(self) -> None:
        """Refresh store configuration from SSM Parameter Store"""
        try:
            stores_param = cast(SSMParameterStore, self._ssm["stores"])
            config = str(stores_param["config"])
            self._store_config = json.loads(config)
        except (ClientError, KeyError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load store configuration: {str(e)}")
            # Fallback to default configuration if SSM fails
            self._store_config = {
                "20400": {
                    "name": "Store 20400",
                    "open_date": "2024-01-31",
                    "close_date": None,
                },
                "20407": {
                    "name": "Store 20407",
                    "open_date": "2024-03-06",
                    "close_date": None,
                },
            }
            logger.warning("Using fallback store configuration")

    def get_active_stores(self, target_date: date) -> list[str]:
        """Get list of stores that were active on a given date."""
        active_stores = []
        for store_id, _config in self._store_config.items():
            if self.is_store_active(store_id, target_date):
                active_stores.append(store_id)
        return sorted(active_stores)  # Sort for consistency

    def is_store_active(self, store_id: str, target_date: date) -> bool:
        """Check if a specific store was active on a given date."""
        if store_id not in self._store_config:
            return False

        config = self._store_config[store_id]
        open_date = date.fromisoformat(config["open_date"])

        if config["close_date"] is not None:
            close_date = date.fromisoformat(config["close_date"])
            return open_date <= target_date <= close_date

        return open_date <= target_date

    def get_store_name(self, store_id: str) -> str | None:
        """Get the name of a store."""
        name: str | None = self._store_config.get(store_id, {}).get("name")
        return name

    def get_store_open_date(self, store_id: str) -> date:
        """Get the open date of a store."""
        return date.fromisoformat(self._store_config.get(store_id, {}).get("open_date"))

    def get_store_ubereats_uuid(self, store_id: str) -> str | None:
        """Get the Uber Eats UUID of a store."""
        uuid: str | None = self._store_config.get(store_id, {}).get("ubereats_uuid")
        return uuid

    def get_inventory_processing_month(self, processing_date: date) -> tuple[int, int]:
        """
        Determine which month and year should be used for inventory processing.

        Business rule: Continue processing the previous month's inventory until
        the second Tuesday of the new month to allow for weekly inventories to be
        completed and posted, while also allowing for late month-end inventory postings.

        Args:
            processing_date: The date when the processing is running

        Returns:
            Tuple of (year, month) that should be processed for inventory
        """
        # Find the first day of the current month
        first_of_month = processing_date.replace(day=1)

        # Find the first Tuesday of the month
        first_tuesday = first_of_month
        while first_tuesday.weekday() != 1:  # 1 is Tuesday
            first_tuesday = first_tuesday.replace(day=first_tuesday.day + 1)

        # Find the second Tuesday of the month
        second_tuesday = first_tuesday.replace(day=first_tuesday.day + 7)

        # If we haven't reached the second Tuesday yet, process previous month
        if processing_date < second_tuesday:
            if processing_date.month == 1:
                # January -> December of previous year
                return (processing_date.year - 1, 12)
            else:
                # Any other month -> previous month of same year
                return (processing_date.year, processing_date.month - 1)
        else:
            # On or after second Tuesday, process current month
            return (processing_date.year, processing_date.month)

    def get_manager_names_by_store(self) -> dict[str, str]:
        """Returns {store_id: manager_name} for stores with a manager configured."""
        result: dict[str, str] = {}
        for store_id, config in self._store_config.items():
            manager_name = config.get("manager_name")
            if manager_name:
                result[store_id] = manager_name
        return result

    @property
    def all_stores(self) -> list[str]:
        """Get list of all store IDs."""
        return sorted(self._store_config.keys())  # Sort for consistency
