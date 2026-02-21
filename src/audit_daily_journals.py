#!/usr/bin/env python3
"""Audit 2025 daily journal files in Google Drive.

This utility script identifies missing files and files with errors (no data content)
for daily journal uploads, with special handling for holidays.

Usage:
    PYTHONPATH=src python src/audit_daily_journals.py --output journal_audit.json --verbose
"""

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any

from store_config import StoreConfig
from wmcgdrive import WMCGdrive

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 2025 holidays when stores are closed (no journal data expected)
HOLIDAYS_2025 = {
    date(2025, 4, 20): "Easter",
    date(2025, 11, 27): "Thanksgiving",
    date(2025, 12, 25): "Christmas",
}

# "No Journal Entry Found" is exactly 21 bytes
NO_DATA_FILE_SIZE = 21

# Regex pattern for parsing journal filenames: YYYY-MM-DD-STORE_daily_journal.txt
FILENAME_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d+)_daily_journal\.txt$")


class FileStatus(Enum):
    """Status of a daily journal file."""

    PRESENT = "present"
    MISSING = "missing"
    NO_DATA = "no_data"  # File <= 21 bytes on non-holiday, action required
    NO_DATA_HOLIDAY = "no_data_holiday"  # File <= 21 bytes on holiday, expected


@dataclass
class FileInfo:
    """Information about a Google Drive file."""

    file_id: str
    filename: str
    size: int


@dataclass
class DateStoreResult:
    """Result for a single date/store combination."""

    audit_date: date
    store: str
    status: FileStatus
    file_info: FileInfo | None = None
    is_holiday: bool = False
    holiday_name: str | None = None


@dataclass
class AuditResult:
    """Complete audit results."""

    run_date: date
    date_range_start: date
    date_range_end: date
    stores_audited: list[str]
    total_expected: int = 0
    total_found: int = 0
    missing: list[DateStoreResult] = field(default_factory=list)
    no_data: list[DateStoreResult] = field(default_factory=list)
    no_data_holiday: list[DateStoreResult] = field(default_factory=list)
    present: list[DateStoreResult] = field(default_factory=list)


def is_holiday(check_date: date) -> tuple[bool, str | None]:
    """Check if a date is a holiday.

    Args:
        check_date: The date to check.

    Returns:
        Tuple of (is_holiday, holiday_name).
    """
    if check_date in HOLIDAYS_2025:
        return True, HOLIDAYS_2025[check_date]
    return False, None


def parse_filename(filename: str) -> tuple[date, str] | None:
    """Parse a journal filename to extract date and store.

    Args:
        filename: The filename to parse (e.g., "2025-01-10-20400_daily_journal.txt").

    Returns:
        Tuple of (date, store) or None if filename doesn't match pattern.
    """
    match = FILENAME_PATTERN.match(filename)
    if match:
        date_str, store = match.groups()
        return date.fromisoformat(date_str), store
    return None


def build_file_lookup(
    files: list[dict[str, Any]], year: int = 2025
) -> dict[tuple[date, str], FileInfo]:
    """Build a lookup dictionary from Google Drive files.

    Args:
        files: List of file dicts with 'id', 'name', 'size' fields.
        year: Filter to only include files from this year.

    Returns:
        Dictionary mapping (date, store) to FileInfo.
    """
    lookup: dict[tuple[date, str], FileInfo] = {}

    for file_data in files:
        parsed = parse_filename(file_data.get("name", ""))
        if parsed:
            file_date, store = parsed
            if file_date.year == year:
                lookup[(file_date, store)] = FileInfo(
                    file_id=file_data.get("id", ""),
                    filename=file_data.get("name", ""),
                    size=int(file_data.get("size", 0)),
                )

    return lookup


def get_audit_date_range(
    start_date: date | None = None, end_date: date | None = None
) -> tuple[date, date]:
    """Get date range for the audit.

    Args:
        start_date: Start date (defaults to 2025-01-01).
        end_date: End date (defaults to yesterday).

    Returns:
        Tuple of (start_date, end_date).
    """
    if start_date is None:
        start_date = date(2025, 1, 1)

    if end_date is None:
        # Default to yesterday
        end_date = min(date.today() - timedelta(days=1), date(2025, 12, 31))

    return start_date, end_date


def audit_journals(
    start_date: date | None = None,
    end_date: date | None = None,
    verbose: bool = False,
) -> AuditResult:
    """Audit daily journal files in Google Drive.

    Args:
        start_date: Start date for audit (defaults to 2025-01-01).
        end_date: End date for audit (defaults to yesterday).
        verbose: Print detailed progress.

    Returns:
        AuditResult with categorized results.
    """
    # Initialize components
    if verbose:
        logger.info("Initializing StoreConfig and Google Drive client...")

    store_config = StoreConfig()
    gdrive = WMCGdrive()

    # Get date range
    start, end = get_audit_date_range(start_date, end_date)
    if verbose:
        logger.info(f"Auditing date range: {start} to {end}")

    # Fetch all journal files from Google Drive
    if verbose:
        logger.info("Fetching journal files from Google Drive...")

    drive_files = gdrive.retrieve_journal_files_with_size()
    if verbose:
        logger.info(f"Found {len(drive_files)} journal files in Google Drive")

    # Build lookup dictionary
    file_lookup = build_file_lookup(drive_files, year=2025)
    if verbose:
        logger.info(f"Parsed {len(file_lookup)} files for 2025")

    # Generate expected date/store combinations
    if verbose:
        logger.info("Generating expected date/store combinations...")

    stores_seen: set[str] = set()
    expected: list[tuple[date, str]] = []
    current = start
    while current <= end:
        active_stores = store_config.get_active_stores(current)
        for store in active_stores:
            expected.append((current, store))
            stores_seen.add(store)
        current += timedelta(days=1)

    if verbose:
        logger.info(f"Generated {len(expected)} expected date/store combinations")
        logger.info(f"Stores audited: {sorted(stores_seen)}")

    # Initialize result
    result = AuditResult(
        run_date=date.today(),
        date_range_start=start,
        date_range_end=end,
        stores_audited=sorted(stores_seen),
        total_expected=len(expected),
    )

    # Compare expected vs actual
    if verbose:
        logger.info("Comparing expected vs actual files...")

    for dt, store in expected:
        file_info = file_lookup.get((dt, store))
        holiday, holiday_name = is_holiday(dt)

        if file_info is None:
            # Missing file
            result.missing.append(
                DateStoreResult(
                    audit_date=dt,
                    store=store,
                    status=FileStatus.MISSING,
                    is_holiday=holiday,
                    holiday_name=holiday_name,
                )
            )
        elif file_info.size <= NO_DATA_FILE_SIZE:
            # File exists but has no data content
            if holiday:
                result.no_data_holiday.append(
                    DateStoreResult(
                        audit_date=dt,
                        store=store,
                        status=FileStatus.NO_DATA_HOLIDAY,
                        file_info=file_info,
                        is_holiday=True,
                        holiday_name=holiday_name,
                    )
                )
            else:
                result.no_data.append(
                    DateStoreResult(
                        audit_date=dt,
                        store=store,
                        status=FileStatus.NO_DATA,
                        file_info=file_info,
                        is_holiday=False,
                    )
                )
        else:
            # File exists with content
            result.present.append(
                DateStoreResult(
                    audit_date=dt,
                    store=store,
                    status=FileStatus.PRESENT,
                    file_info=file_info,
                    is_holiday=holiday,
                    holiday_name=holiday_name,
                )
            )

    result.total_found = (
        len(result.present) + len(result.no_data) + len(result.no_data_holiday)
    )

    if verbose:
        logger.info("Audit complete:")
        logger.info(f"  Total expected: {result.total_expected}")
        logger.info(f"  Total found: {result.total_found}")
        logger.info(f"  Missing: {len(result.missing)}")
        logger.info(f"  No data (action needed): {len(result.no_data)}")
        logger.info(f"  No data on holidays (expected): {len(result.no_data_holiday)}")
        logger.info(f"  Present with content: {len(result.present)}")

    return result


def generate_output_json(result: AuditResult) -> dict[str, Any]:
    """Generate output JSON from audit result.

    Args:
        result: The audit result.

    Returns:
        Dictionary ready for JSON serialization.
    """
    # Build rerun payload - group by date for missing and no_data files
    rerun_dates: dict[str, list[str]] = {}
    for item in result.missing + result.no_data:
        date_str = item.audit_date.isoformat()
        if date_str not in rerun_dates:
            rerun_dates[date_str] = []
        rerun_dates[date_str].append(item.store)

    # Sort and format rerun payload
    rerun_payload = [
        {"date": dt, "stores": sorted(stores)}
        for dt, stores in sorted(rerun_dates.items())
    ]

    return {
        "audit_metadata": {
            "audit_date": result.run_date.isoformat(),
            "date_range": {
                "start": result.date_range_start.isoformat(),
                "end": result.date_range_end.isoformat(),
            },
            "stores_audited": result.stores_audited,
            "total_expected_files": result.total_expected,
            "total_found_files": result.total_found,
            "holidays": [
                {"date": dt.isoformat(), "name": name}
                for dt, name in sorted(HOLIDAYS_2025.items())
            ],
        },
        "summary": {
            "missing_count": len(result.missing),
            "no_data_count": len(result.no_data),
            "holiday_no_data_count": len(result.no_data_holiday),
            "present_count": len(result.present),
        },
        "missing_files": [
            {
                "date": item.audit_date.isoformat(),
                "store": item.store,
                "expected_filename": f"{item.audit_date.isoformat()}-{item.store}_daily_journal.txt",
                "is_holiday": item.is_holiday,
                "holiday_name": item.holiday_name,
            }
            for item in sorted(result.missing, key=lambda x: (x.audit_date, x.store))
        ],
        "no_data_files": [
            {
                "date": item.audit_date.isoformat(),
                "store": item.store,
                "filename": item.file_info.filename if item.file_info else None,
                "file_id": item.file_info.file_id if item.file_info else None,
                "size_bytes": item.file_info.size if item.file_info else None,
                "action_required": True,
            }
            for item in sorted(result.no_data, key=lambda x: (x.audit_date, x.store))
        ],
        "holiday_no_data_files": [
            {
                "date": item.audit_date.isoformat(),
                "store": item.store,
                "filename": item.file_info.filename if item.file_info else None,
                "file_id": item.file_info.file_id if item.file_info else None,
                "size_bytes": item.file_info.size if item.file_info else None,
                "holiday_name": item.holiday_name,
                "action_required": False,
            }
            for item in sorted(
                result.no_data_holiday, key=lambda x: (x.audit_date, x.store)
            )
        ],
        "rerun_payload": {
            "description": "Payload for re-running daily_journal Lambda for missing/no-data dates",
            "dates": rerun_payload,
        },
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Audit 2025 daily journal files in Google Drive"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="journal_audit_2025.json",
        help="Output JSON file path (default: journal_audit_2025.json)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed progress",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2025-01-01",
        help="Start date (YYYY-MM-DD, default: 2025-01-01)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date (YYYY-MM-DD, default: yesterday)",
    )

    args = parser.parse_args()

    # Parse dates
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date) if args.end_date else None

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # Run audit
        result = audit_journals(
            start_date=start_date,
            end_date=end_date,
            verbose=args.verbose,
        )

        # Generate output JSON
        output = generate_output_json(result)

        # Write to file
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)

        # Print summary
        print(f"\nAudit complete. Results saved to {args.output}")
        print(f"  Date range: {result.date_range_start} to {result.date_range_end}")
        print(f"  Stores audited: {', '.join(result.stores_audited)}")
        print(f"  Total expected: {result.total_expected}")
        print(f"  Total found: {result.total_found}")
        print(f"  Missing files: {len(result.missing)}")
        print(f"  No data files (action needed): {len(result.no_data)}")
        print(f"  Holiday no data files (expected): {len(result.no_data_holiday)}")
        print(f"  Present with content: {len(result.present)}")

        if result.missing or result.no_data:
            print(
                f"\n  Files needing re-run: {len(result.missing) + len(result.no_data)}"
            )

        return 0

    except Exception as e:
        logger.error(f"Audit failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
