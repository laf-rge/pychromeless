#!/usr/bin/env python3
"""Re-run daily journal fetch for specific dates/stores.

This utility script reads from an audit JSON file and re-fetches daily journal
data from FlexePOS for missing or no-data entries, then uploads to Google Drive.

Usage:
    PYTHONPATH=src python src/rerun_daily_journals.py --audit-file journal_audit_2025.json
    PYTHONPATH=src python src/rerun_daily_journals.py --date 2025-01-27 --store 20407
"""

import argparse
import json
import logging
import sys
from datetime import date
from time import sleep
from typing import Any

from flexepos import Flexepos
from wmcgdrive import WMCGdrive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def rerun_daily_journal(
    target_date: date,
    stores: list[str],
    flexepos: Flexepos,
    gdrive: WMCGdrive,
    dry_run: bool = False,
) -> dict[str, bool]:
    """Re-run daily journal fetch for a specific date and stores.

    Args:
        target_date: The date to fetch journal data for.
        stores: List of store IDs to fetch.
        flexepos: Initialized Flexepos instance.
        gdrive: Initialized WMCGdrive instance.
        dry_run: If True, don't actually upload to Google Drive.

    Returns:
        Dictionary mapping store IDs to success status.
    """
    results: dict[str, bool] = {}
    date_str = target_date.strftime("%m%d%Y")

    logger.info(f"Fetching daily journal for {target_date} stores: {stores}")

    try:
        journal_data = flexepos.getDailyJournal(stores, date_str)

        for store in stores:
            if store not in journal_data:
                logger.warning(f"No data returned for store {store} on {target_date}")
                results[store] = False
                continue

            content = journal_data[store]
            content_size = len(content.encode("utf-8"))

            # Check if we got actual data (more than "No Journal Entry Found")
            if content_size <= 21:
                logger.warning(
                    f"Store {store} on {target_date}: No journal data "
                    f"(size: {content_size} bytes)"
                )
                results[store] = False
                continue

            filename = f"{target_date}-{store}_daily_journal.txt"

            if dry_run:
                logger.info(f"[DRY RUN] Would upload {filename} ({content_size} bytes)")
                results[store] = True
            else:
                logger.info(f"Uploading {filename} ({content_size} bytes)")
                gdrive.upload(filename, content.encode("utf-8"), "text/plain")
                results[store] = True
                logger.info(f"Successfully uploaded {filename}")

    except Exception as e:
        logger.error(f"Error fetching journal for {target_date}: {e}")
        for store in stores:
            if store not in results:
                results[store] = False

    return results


def load_rerun_payload(audit_file: str) -> list[dict[str, Any]]:
    """Load rerun payload from audit JSON file.

    Args:
        audit_file: Path to the audit JSON file.

    Returns:
        List of dicts with 'date' and 'stores' keys.
    """
    with open(audit_file) as f:
        data = json.load(f)

    result: list[dict[str, Any]] = data.get("rerun_payload", {}).get("dates", [])
    return result


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Re-run daily journal fetch for specific dates/stores"
    )
    parser.add_argument(
        "--audit-file",
        "-a",
        help="Path to audit JSON file to read rerun_payload from",
    )
    parser.add_argument(
        "--date",
        "-d",
        type=str,
        help="Specific date to rerun (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--store",
        "-s",
        type=str,
        action="append",
        help="Specific store(s) to rerun (can be specified multiple times)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't upload to Google Drive, just show what would be done",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between date fetches (default: 2.0)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.audit_file and not args.date:
        parser.error("Either --audit-file or --date must be specified")

    if args.date and not args.store:
        parser.error("--store must be specified when using --date")

    # Build list of date/store combinations to process
    tasks: list[tuple[date, list[str]]] = []

    if args.audit_file:
        logger.info(f"Loading rerun payload from {args.audit_file}")
        payload = load_rerun_payload(args.audit_file)
        for entry in payload:
            target_date = date.fromisoformat(entry["date"])
            stores = entry["stores"]
            # Filter by specific store if provided
            if args.store:
                stores = [s for s in stores if s in args.store]
            if stores:
                tasks.append((target_date, stores))
        logger.info(f"Loaded {len(tasks)} date/store combinations to process")

    if args.date:
        target_date = date.fromisoformat(args.date)
        tasks.append((target_date, args.store))

    if not tasks:
        logger.info("No tasks to process")
        return 0

    # Initialize services
    logger.info("Initializing FlexePOS and Google Drive clients...")
    flexepos = Flexepos()
    gdrive = WMCGdrive()

    # Process each date
    total_success = 0
    total_failed = 0

    for i, (target_date, stores) in enumerate(tasks):
        if i > 0:
            logger.info(f"Waiting {args.delay} seconds before next fetch...")
            sleep(args.delay)

        results = rerun_daily_journal(
            target_date=target_date,
            stores=stores,
            flexepos=flexepos,
            gdrive=gdrive,
            dry_run=args.dry_run,
        )

        for store, success in results.items():
            if success:
                total_success += 1
            else:
                total_failed += 1

    # Print summary
    print("\nRerun complete:")
    print(f"  Successful: {total_success}")
    print(f"  Failed: {total_failed}")

    if args.dry_run:
        print("\n  (DRY RUN - no uploads were performed)")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
