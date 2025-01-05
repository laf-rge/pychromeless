from datetime import date
from typing import Optional, Dict, List, cast
import json
import logging
from ssm_parameter_store import SSMParameterStore

logger = logging.getLogger(__name__)


class StoreConfig:
    def __init__(self, prefix: str = "/prod"):
        self._store_config: Dict = {}
        self._ssm = SSMParameterStore(prefix=prefix)
        self.refresh()

    def refresh(self) -> None:
        """Refresh store configuration from SSM Parameter Store"""
        try:
            stores_param = cast(SSMParameterStore, self._ssm["stores"])
            config = str(stores_param["config"])
            self._store_config = json.loads(config)
        except Exception as e:
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

    def get_active_stores(self, target_date: date) -> List[str]:
        """Get list of stores that were active on a given date."""
        active_stores = []
        for store_id, config in self._store_config.items():
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

    def get_store_name(self, store_id: str) -> Optional[str]:
        """Get the name of a store."""
        return self._store_config.get(store_id, {}).get("name")

    @property
    def all_stores(self) -> List[str]:
        """Get list of all store IDs."""
        return sorted(self._store_config.keys())  # Sort for consistency
