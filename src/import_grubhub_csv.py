#!/usr/bin/env python3
"""
Helper script to import Grubhub deposits from CSV export into QuickBooks.

Usage:
    python src/import_grubhub_csv.py <csv_filename>

Example:
    python src/import_grubhub_csv.py src/deposit-4861dfa0-da09-11f0-9fa1-7dea75129edb.csv
"""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import qb
from grubhub import Grubhub
from logging_utils import setup_json_logger

# Setup logging
if "AWS_LAMBDA_FUNCTION_NAME" not in sys.modules:
    setup_json_logger()
logger = logging.getLogger(__name__)


def main():
    """Main function to import Grubhub deposits from CSV."""
    parser = argparse.ArgumentParser(
        description="Import Grubhub deposits from CSV export into QuickBooks"
    )
    parser.add_argument(
        "csv_file",
        type=str,
        help="Path to the Grubhub deposit CSV export file",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for filtering deposits (YYYY-MM-DD). Defaults to 14 days ago.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for filtering deposits (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and display deposits without importing to QuickBooks",
    )

    args = parser.parse_args()

    # Validate CSV file exists
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        logger.error("CSV file not found: %s", args.csv_file)
        sys.exit(1)

    # Parse date arguments
    if args.start_date:
        try:
            start_date = date.fromisoformat(args.start_date)
        except ValueError:
            logger.error("Invalid start date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        start_date = date.today() - timedelta(days=14)

    if args.end_date:
        try:
            end_date = date.fromisoformat(args.end_date)
        except ValueError:
            logger.error("Invalid end date format. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        end_date = date.today()

    logger.info(
        "Starting Grubhub CSV import",
        extra={
            "csv_file": str(csv_path),
            "start_date": str(start_date),
            "end_date": str(end_date),
            "dry_run": args.dry_run,
        },
    )

    # Initialize Grubhub and parse CSV
    try:
        gh = Grubhub()
        results = gh.get_payments_from_csv(str(csv_path), start_date, end_date)
        logger.info("Parsed CSV file", extra={"deposit_count": len(results)})
    except Exception as e:
        logger.exception("Error parsing CSV file: %s", str(csv_path))
        sys.exit(1)

    if not results:
        logger.warning("No deposits found in CSV file for the specified date range")
        return 0

    # Display deposits
    print(f"\nFound {len(results)} deposit(s) to process:\n")
    for i, result in enumerate(results, 1):
        service, txdate, notes, lines, store = result
        total_amount = lines[0][2] if lines else "0"
        print(f"  {i}. Store {store} - {txdate} - ${total_amount}")

    if args.dry_run:
        print("\n[DRY RUN] Would import the following deposits:\n")
        for result in results:
            service, txdate, notes, lines, store = result
            print(f"  Store: {store}, Date: {txdate}")
            print(f"  Notes: {notes if notes else '(none)'}")
            print("  Lines:")
            for line in lines:
                account_code, description, amount = line
                print(f"    - Account {account_code}: {description} = ${amount}")
            print()
        return 0

    # Import deposits to QuickBooks
    print("\nImporting deposits to QuickBooks...\n")
    success_count = 0
    error_count = 0

    for result in results:
        service, txdate, notes, lines, store = result
        try:
            # Unpack result: ["Grubhub", txdate, notes, lines, store]
            # sync_third_party_deposit expects: supplier, deposit_date, notes, lines, department
            qb.sync_third_party_deposit(service, txdate, notes, lines, store)
            logger.info(
                "Successfully imported deposit",
                extra={"store": store, "date": str(txdate), "amount": lines[0][2]},
            )
            print(f"  ✓ Imported: Store {store} - {txdate} - ${lines[0][2]}")
            success_count += 1
        except Exception as e:
            logger.exception(
                "Failed to import deposit",
                extra={
                    "store": store,
                    "date": str(txdate),
                    "error": str(e),
                    "result": result,
                },
            )
            print(f"  ✗ Failed: Store {store} - {txdate} - Error: {e}")
            error_count += 1

    print(f"\nImport complete: {success_count} succeeded, {error_count} failed")
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

