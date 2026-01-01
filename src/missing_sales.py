import logging
from datetime import date, timedelta
from typing import Any

from quickbooks.helpers import qb_date_format
from quickbooks.objects import Department, SalesReceipt

import qb
from flexepos import Flexepos
from qb import refresh_session
from store_config import StoreConfig

logger = logging.getLogger(__name__)


def find_missing_sales_entries(
    days_back: int = 60,
    store_config: StoreConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Find missing daily sales entries for each store for each day in the last N days, excluding today.

    Args:
        days_back (int): Number of days to look back from yesterday (default: 60)
        store_config (StoreConfig, optional): StoreConfig instance to use. If None, a new one is created.

    Returns:
        List[Dict[str, Any]]: List of dicts with keys 'stores' (list of missing store IDs) and 'txdate' (date object)
    """
    qb_session = refresh_session()
    if store_config is None:
        store_config = StoreConfig()

    today = date.today()
    missing = []

    # Get all store refs from QuickBooks
    _store_refs = {  # noqa: F841
        x.Name: x.to_ref() for x in Department.all(qb=qb_session)
    }

    for day_offset in range(1, days_back + 1):  # Start at 1 to skip today
        txdate = today - timedelta(days=day_offset)
        active_stores = store_config.get_active_stores(txdate)
        # Query all receipts for this date
        receipts = SalesReceipt.filter(TxnDate=qb_date_format(txdate), qb=qb)
        receipts_by_store = set()
        for r in receipts:
            if r.DepartmentRef and hasattr(r.DepartmentRef, "name"):
                receipts_by_store.add(r.DepartmentRef.name)
        # Find missing stores
        missing_stores = [s for s in active_stores if s not in receipts_by_store]
        if missing_stores:
            missing.append({"stores": missing_stores, "txdate": txdate})
    return missing


def fill_missing_sales_entries(
    days_back: int = 60, store_config: StoreConfig | None = None
) -> None:
    """
    Find and fill missing daily sales entries for each store for each day in the last N days.

    Args:
        days_back (int): Number of days to look back from today (default: 60)
        store_config (StoreConfig, optional): StoreConfig instance to use. If None, a new one is created.
    """
    logger.info(f"Checking for missing sales entries for the last {days_back} days...")
    missing = find_missing_sales_entries(days_back=days_back, store_config=store_config)
    dj = Flexepos()
    filled_count = 0
    for m in missing:
        txdate = m["txdate"]
        for store in m["stores"]:
            try:
                logger.info(f"Filling missing sales for store {store} on {txdate}")
                sales_data = dj.getDailySales(store, txdate)
                qb.create_daily_sales(txdate, sales_data)
                filled_count += 1
            except Exception as e:
                logger.exception(
                    f"Failed to fill sales for store {store} on {txdate}: {e}"
                )
    logger.info(f"Filled {filled_count} missing sales entries.")
