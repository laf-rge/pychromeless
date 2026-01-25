#!/usr/bin/env python3
"""
Backfill daily sales for dates affected by the third-party scraping bug.
Runs sequentially to avoid overwhelming FlexePOS and QuickBooks.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from datetime import date, timedelta
import time

from lambda_function import daily_sales_handler


def main():
    # Affected dates: 12/29/2025 through 01/18/2026
    start_date = date(2025, 12, 29)
    end_date = date(2026, 1, 18)

    current_date = start_date
    dates_to_process = []

    while current_date <= end_date:
        dates_to_process.append(current_date)
        current_date += timedelta(days=1)

    total = len(dates_to_process)
    print(f"Starting backfill for {total} dates: {start_date} to {end_date}")
    print("=" * 60)

    for i, tx_date in enumerate(dates_to_process, 1):
        print(f"\n[{i}/{total}] Processing {tx_date.isoformat()}...")
        print("-" * 40)

        event = {
            "year": str(tx_date.year),
            "month": str(tx_date.month).zfill(2),
            "day": str(tx_date.day).zfill(2),
        }

        try:
            start_time = time.time()
            result = daily_sales_handler(event)
            elapsed = time.time() - start_time

            status = result.get("statusCode", "unknown")
            print(f"  Result: status={status}, elapsed={elapsed:.1f}s")

            if status != 200:
                print(f"  WARNING: Non-200 status code!")
                print(f"  Body: {result.get('body', 'no body')[:200]}")
        except Exception as e:
            print(f"  ERROR: {e}")

        # Wait between dates to avoid rate limiting
        if i < total:
            wait_time = 30  # 30 seconds between dates
            print(f"  Waiting {wait_time}s before next date...")
            time.sleep(wait_time)

    print("\n" + "=" * 60)
    print("Backfill complete!")


if __name__ == "__main__":
    main()
