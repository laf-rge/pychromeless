"""
Payroll Allocation Module

This module handles the monthly payroll allocation process:
1. Parse Gusto "Total By Location" CSV
2. Aggregate payroll data by store using address/zip mapping
3. Create journal entry to allocate payroll from NOT SPECIFIED to stores
"""

import calendar
import csv
import datetime
import io
import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from quickbooks.helpers import qb_date_format
from quickbooks.objects.journalentry import (
    JournalEntry,
    JournalEntryLine,
    JournalEntryLineDetail,
)

import qb
from decimal_utils import TWO_PLACES
from qb import get_store_refs, refresh_session, wmc_account_ref

logger = logging.getLogger(__name__)

# Address-to-Store mapping (zip code -> store ID)
# Can be loaded from SSM Parameter Store in production
STORE_ADDRESS_MAP: dict[str, str | None] = {
    "94954": "20395",  # Petaluma - 201 S McDowell Blvd
    "95407": "20358",  # Santa Rosa Ave - 2688 Santa Rosa Ave
    "95403": "20400",  # Hopper Ave - 919 Hopper Ave
    "94931": "20407",  # Cotati - 640 E Cotati Ave
    "94928": "WMC",  # Rohnert Park - Central Office (corporate)
}

# QBO Account Numbers (AcctNum) for payroll allocation
# Discovered from examining existing labor-YYYY-MM journal entries and querying accounts
# Note: These are AcctNum values, NOT internal QBO IDs
PAYROLL_ACCOUNTS = {
    "officer_wages": "5500",  # Payroll Expenses Labor:Officer Wages
    "employer_taxes": "5520",  # Payroll Expenses Labor:Payroll Taxes - Employer
    "wages": "5502",  # Payroll Expenses Labor:Payroll Expenses - Hourly:Wages
    "overtime": "5504",  # Payroll Expenses Labor:Payroll Expenses - Hourly:Overtime
    "vacation_pay": "5507",  # Payroll Expenses Labor:Payroll Expenses - Hourly:Vacation Pay
    "sick_pay": "5508",  # Payroll Expenses Labor:Payroll Expenses - Hourly:Sick Pay
    "meal_violations": "5505",  # Payroll Expenses Labor:Payroll Expenses - Hourly:Meal period violations
    "medical_insurance": "5531",  # Payroll Expenses Labor:Employee Benefits:Medical Insurance
    "dental_insurance": "5532",  # Payroll Expenses Labor:Employee Benefits:Dental Insurance
    "hsa": "5534",  # Payroll Expenses Labor:Employee Benefits:HSA
    "life_insurance": "5533",  # Payroll Expenses Labor:Employee Benefits:Life Insurance
    "travel_reimbursement": "6152",  # Expenses:Travel & Ent:Travel (source for reimbursements)
    "store_supplies": "6059",  # Expenses:Management Control:Supplies:Store Supplies (dest)
}

# Store departments in the order they appear in journal entries
STORE_ORDER = ["WMC", "20358", "20395", "20400", "20407"]


@dataclass
class PayrollData:
    """Aggregated payroll data for a store."""

    gross_earnings: Decimal = field(default_factory=lambda: Decimal("0.00"))
    employer_taxes: Decimal = field(default_factory=lambda: Decimal("0.00"))
    regular_earnings: Decimal = field(default_factory=lambda: Decimal("0.00"))
    overtime_earnings: Decimal = field(default_factory=lambda: Decimal("0.00"))
    double_overtime_earnings: Decimal = field(default_factory=lambda: Decimal("0.00"))
    pto_earnings: Decimal = field(default_factory=lambda: Decimal("0.00"))
    sick_earnings: Decimal = field(default_factory=lambda: Decimal("0.00"))
    holiday_earnings: Decimal = field(default_factory=lambda: Decimal("0.00"))
    bonus: Decimal = field(default_factory=lambda: Decimal("0.00"))
    vision_insurance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    dental_insurance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    dental_insurance_dependents: Decimal = field(
        default_factory=lambda: Decimal("0.00")
    )
    medical_insurance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    medical_insurance_dependents: Decimal = field(
        default_factory=lambda: Decimal("0.00")
    )
    employer_contributions: Decimal = field(default_factory=lambda: Decimal("0.00"))
    reimbursements: Decimal = field(default_factory=lambda: Decimal("0.00"))
    paycheck_tips: Decimal = field(default_factory=lambda: Decimal("0.00"))
    life_insurance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    hsa: Decimal = field(default_factory=lambda: Decimal("0.00"))
    # New columns from enhanced Gusto report
    officer_wages: Decimal = field(default_factory=lambda: Decimal("0.00"))
    meal_period_violations: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def add(self, other: "PayrollData") -> None:
        """Add another PayrollData to this one."""
        self.gross_earnings += other.gross_earnings
        self.employer_taxes += other.employer_taxes
        self.regular_earnings += other.regular_earnings
        self.overtime_earnings += other.overtime_earnings
        self.double_overtime_earnings += other.double_overtime_earnings
        self.pto_earnings += other.pto_earnings
        self.sick_earnings += other.sick_earnings
        self.holiday_earnings += other.holiday_earnings
        self.bonus += other.bonus
        self.vision_insurance += other.vision_insurance
        self.dental_insurance += other.dental_insurance
        self.dental_insurance_dependents += other.dental_insurance_dependents
        self.medical_insurance += other.medical_insurance
        self.medical_insurance_dependents += other.medical_insurance_dependents
        self.employer_contributions += other.employer_contributions
        self.reimbursements += other.reimbursements
        self.paycheck_tips += other.paycheck_tips
        self.life_insurance += other.life_insurance
        self.hsa += other.hsa
        self.officer_wages += other.officer_wages
        self.meal_period_violations += other.meal_period_violations


def get_journal_entries_by_pattern(pattern: str, max_results: int = 10) -> list[Any]:
    """
    Retrieve journal entries matching a DocNumber pattern.

    Args:
        pattern: SQL LIKE pattern for DocNumber (e.g., "labor-%")
        max_results: Maximum number of results to return

    Returns:
        List of JournalEntry objects
    """
    refresh_session()
    entries = JournalEntry.where(
        f"DocNumber LIKE '{pattern}'",
        qb=qb.CLIENT,
        max_results=max_results,
        order_by="DocNumber DESC",
    )
    return entries


def get_journal_entry_by_doc_number(doc_number: str) -> JournalEntry | None:
    """
    Retrieve a specific journal entry by DocNumber.

    Args:
        doc_number: The exact DocNumber to find (e.g., "labor-2025-11")

    Returns:
        JournalEntry if found, None otherwise
    """
    refresh_session()
    entries = JournalEntry.where(
        f"DocNumber = '{doc_number}'",
        qb=qb.CLIENT,
    )
    return entries[0] if entries else None


def journal_entry_to_dict(entry: JournalEntry) -> dict[str, Any]:
    """
    Convert a JournalEntry to a readable dictionary format.

    Args:
        entry: The JournalEntry object

    Returns:
        Dictionary with key journal entry information
    """
    lines = []
    for line in entry.Line or []:
        detail = line.JournalEntryLineDetail
        lines.append(
            {
                "line_num": line.LineNum,
                "amount": str(line.Amount),
                "description": line.Description,
                "posting_type": detail.PostingType if detail else None,
                "account": (
                    detail.AccountRef.name if detail and detail.AccountRef else None
                ),
                "account_id": (
                    detail.AccountRef.value if detail and detail.AccountRef else None
                ),
                "department": (
                    detail.DepartmentRef.name
                    if detail and detail.DepartmentRef
                    else "NOT SPECIFIED"
                ),
            }
        )

    return {
        "id": entry.Id,
        "doc_number": entry.DocNumber,
        "txn_date": str(entry.TxnDate),
        "private_note": entry.PrivateNote,
        "total_amount": str(entry.TotalAmt) if hasattr(entry, "TotalAmt") else None,
        "lines": lines,
    }


def examine_labor_journal_entries(count: int = 3) -> list[dict[str, Any]]:
    """
    Retrieve and examine recent labor journal entries.

    This is used to understand the structure of existing entries
    before creating new ones.

    Args:
        count: Number of entries to retrieve

    Returns:
        List of journal entry dictionaries
    """
    entries = get_journal_entries_by_pattern("labor-%", max_results=count)
    return [journal_entry_to_dict(entry) for entry in entries]


def parse_gusto_csv(csv_content: bytes) -> dict[str, PayrollData]:
    """
    Parse Gusto "Total By Location" CSV and aggregate by store.

    Args:
        csv_content: Raw CSV file content

    Returns:
        Dictionary mapping store ID to PayrollData
    """
    result: dict[str, PayrollData] = {}

    # Decode CSV content
    content = csv_content.decode("utf-8-sig")  # Handle BOM if present

    # The Gusto CSV has header lines before the actual data
    # Find the line that starts with "Payroll," which is the real CSV header
    lines = content.split("\n")
    csv_start_index = 0
    for i, line in enumerate(lines):
        if line.startswith("Payroll,"):
            csv_start_index = i
            break

    # Use only the CSV portion (from the header row onwards)
    csv_content_clean = "\n".join(lines[csv_start_index:])
    reader = csv.DictReader(io.StringIO(csv_content_clean))

    for row in reader:
        # Skip header rows and empty rows
        if not row.get("Work address (zip)"):
            continue

        # Skip the "Grand totals" row
        if row.get("Payroll", "").startswith("Grand totals"):
            continue

        # Map zip code to store ID
        zip_code = row.get("Work address (zip)", "").strip()
        store_id = STORE_ADDRESS_MAP.get(zip_code)

        if store_id is None:
            logger.warning(
                "Unknown zip code in Gusto CSV",
                extra={"zip_code": zip_code},
            )
            continue

        # Initialize store data if not exists
        if store_id not in result:
            result[store_id] = PayrollData()

        # Parse and add payroll data
        def parse_decimal(value: str) -> Decimal:
            try:
                return Decimal(value.strip() or "0").quantize(TWO_PLACES)
            except Exception:
                return Decimal("0.00")

        employee_data = PayrollData(
            gross_earnings=parse_decimal(row.get("Gross earnings", "0")),
            employer_taxes=parse_decimal(row.get("Total employer taxes", "0")),
            regular_earnings=parse_decimal(row.get("Regular earnings", "0")),
            overtime_earnings=parse_decimal(row.get("Overtime earnings", "0")),
            double_overtime_earnings=parse_decimal(
                row.get("Double overtime earnings", "0")
            ),
            pto_earnings=parse_decimal(row.get("Paid time off earnings", "0")),
            sick_earnings=parse_decimal(row.get("Sick time off earnings", "0")),
            holiday_earnings=parse_decimal(row.get("Holiday earnings", "0")),
            bonus=parse_decimal(row.get("Bonus", "0")),
            vision_insurance=parse_decimal(
                row.get("Employee Vision Insurance (employer)", "0")
            ),
            dental_insurance=parse_decimal(
                row.get("Employee Dental Insurance (employer)", "0")
            ),
            dental_insurance_dependents=parse_decimal(
                row.get("Dependents Dental Insurance (employer)", "0")
            ),
            medical_insurance=parse_decimal(
                row.get("Employee Medical Insurance (employer)", "0")
            ),
            medical_insurance_dependents=parse_decimal(
                row.get("Dependents Medical Insurance (employer)", "0")
            ),
            employer_contributions=parse_decimal(
                row.get("Total employer contributions", "0")
            ),
            reimbursements=parse_decimal(row.get("Total reimbursements", "0")),
            paycheck_tips=parse_decimal(row.get("Paycheck tips", "0")),
            life_insurance=parse_decimal(
                row.get("Employee Life Insurance (employer)", "0")
            ),
            hsa=parse_decimal(row.get("Health Savings Account (employer)", "0")),
            officer_wages=parse_decimal(row.get("Officer Wages", "0")),
            meal_period_violations=parse_decimal(
                row.get("Meal Period Violations", "0")
            ),
        )

        result[store_id].add(employee_data)

    return result


def _add_account_lines(
    lines: list[JournalEntryLine],
    account_num: str,
    store_amounts: dict[str, Decimal],
    store_refs: dict[str, Any],
) -> None:
    """
    Add journal entry lines for a single account.

    Creates one Credit line for the total (NOT SPECIFIED) and
    one Debit line per store with non-zero amounts.

    Args:
        lines: List to append lines to
        account_num: The AcctNum for the account
        store_amounts: Dictionary mapping store ID to amount
        store_refs: Dictionary mapping store name to DepartmentRef
    """
    # Calculate total
    total = sum(store_amounts.values())
    if total == Decimal("0.00"):
        return

    # Add Credit line for NOT SPECIFIED (total)
    credit_line = JournalEntryLine()
    credit_line.JournalEntryLineDetail = JournalEntryLineDetail()
    credit_line.JournalEntryLineDetail.AccountRef = wmc_account_ref(account_num)
    credit_line.JournalEntryLineDetail.PostingType = "Credit"
    credit_line.JournalEntryLineDetail.DepartmentRef = None  # NOT SPECIFIED
    credit_line.Amount = total.quantize(TWO_PLACES)
    lines.append(credit_line)

    # Add Debit lines for each store (in order)
    for store_id in STORE_ORDER:
        amount = store_amounts.get(store_id, Decimal("0.00"))
        # Include zero amounts to match existing journal entry format
        debit_line = JournalEntryLine()
        debit_line.JournalEntryLineDetail = JournalEntryLineDetail()
        debit_line.JournalEntryLineDetail.AccountRef = wmc_account_ref(account_num)
        debit_line.JournalEntryLineDetail.PostingType = "Debit"
        debit_line.JournalEntryLineDetail.DepartmentRef = store_refs.get(store_id)
        debit_line.Amount = amount.quantize(TWO_PLACES)
        lines.append(debit_line)


class JournalEntryExistsError(Exception):
    """Raised when a journal entry already exists and allow_update is False."""

    def __init__(self, doc_number: str, entry_id: str, entry_url: str):
        self.doc_number = doc_number
        self.entry_id = entry_id
        self.entry_url = entry_url
        super().__init__(
            f"Journal entry {doc_number} already exists (ID: {entry_id}). "
            f"Review at: {entry_url}"
        )


def create_payroll_allocation_journal(
    year: int,
    month: int,
    payroll_by_store: dict[str, PayrollData],
    allow_update: bool = False,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Create a payroll allocation journal entry.

    Args:
        year: The year (e.g., 2025)
        month: The month (1-12)
        payroll_by_store: Dictionary mapping store ID to PayrollData
        allow_update: If True, allow updating an existing entry. If False (default),
                      raise JournalEntryExistsError if entry already exists.

    Returns:
        Tuple of (QBO journal entry URL, list of warnings)

    Raises:
        JournalEntryExistsError: If entry exists and allow_update is False
    """
    refresh_session()

    doc_number = f"labor-{year}-{str(month).zfill(2)}"
    warnings: list[dict[str, Any]] = []

    # Check if entry already exists
    existing = get_journal_entry_by_doc_number(doc_number)
    if existing:
        existing_url = f"https://app.qbo.intuit.com/app/journal?txnId={existing.Id}"
        if not allow_update:
            raise JournalEntryExistsError(doc_number, existing.Id, existing_url)
        # User explicitly allowed update - clear existing lines
        jentry = existing
        jentry.Line = []
        logger.info(
            "Updating existing journal entry",
            extra={"doc_number": doc_number, "entry_id": existing.Id},
        )
    else:
        jentry = JournalEntry()
        jentry.DocNumber = doc_number

    # Set transaction date to last day of month
    last_day = calendar.monthrange(year, month)[1]
    jentry.TxnDate = qb_date_format(datetime.date(year, month, last_day))

    # Add note indicating this was generated by Josiah
    run_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    jentry.PrivateNote = (
        f"Generated by Josiah from Gusto Total By Location CSV on {run_date}"
    )

    # Get store department references
    store_refs = get_store_refs()

    lines: list[JournalEntryLine] = []

    # 1. Officer Wages - use direct value from Gusto if available, else calculate
    # (Officer wages = gross - life_insurance when calculated)
    officer_wages_by_store = {
        store: data.officer_wages for store, data in payroll_by_store.items()
    }
    # If no direct officer wages in CSV, fall back to calculated value for WMC
    total_officer_wages = sum(officer_wages_by_store.values())
    if total_officer_wages == Decimal("0.00"):
        # Fallback: calculate from WMC gross - life_insurance
        wmc_data = payroll_by_store.get("WMC", PayrollData())
        calculated_officer_wages = wmc_data.gross_earnings - wmc_data.life_insurance
        if calculated_officer_wages > Decimal("0.00"):
            officer_wages_by_store = {"WMC": calculated_officer_wages}
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["officer_wages"],
        officer_wages_by_store,
        store_refs,
    )

    # 2. Employer Taxes - all stores
    employer_taxes_by_store = {
        store: data.employer_taxes for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["employer_taxes"],
        employer_taxes_by_store,
        store_refs,
    )

    # 3. Hourly Wages - all stores
    wages_by_store = {
        store: data.regular_earnings for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["wages"],
        wages_by_store,
        store_refs,
    )

    # 4. Overtime - all stores
    overtime_by_store = {
        store: data.overtime_earnings + data.double_overtime_earnings
        for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["overtime"],
        overtime_by_store,
        store_refs,
    )

    # 5. Vacation Pay (includes PTO and holiday)
    vacation_by_store = {
        store: data.pto_earnings + data.holiday_earnings
        for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["vacation_pay"],
        vacation_by_store,
        store_refs,
    )

    # 6. Sick Pay
    sick_by_store = {
        store: data.sick_earnings for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["sick_pay"],
        sick_by_store,
        store_refs,
    )

    # 7. Meal Period Violations
    mpv_by_store = {
        store: data.meal_period_violations for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["meal_violations"],
        mpv_by_store,
        store_refs,
    )

    # 8. Medical Insurance (employee + dependents)
    medical_by_store = {
        store: data.medical_insurance + data.medical_insurance_dependents
        for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["medical_insurance"],
        medical_by_store,
        store_refs,
    )

    # 9. Dental Insurance (employee + dependents)
    dental_by_store = {
        store: data.dental_insurance + data.dental_insurance_dependents
        for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["dental_insurance"],
        dental_by_store,
        store_refs,
    )

    # 10. HSA
    hsa_by_store = {store: data.hsa for store, data in payroll_by_store.items()}
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["hsa"],
        hsa_by_store,
        store_refs,
    )

    # 11. Life Insurance
    life_by_store = {
        store: data.life_insurance for store, data in payroll_by_store.items()
    }
    _add_account_lines(
        lines,
        PAYROLL_ACCOUNTS["life_insurance"],
        life_by_store,
        store_refs,
    )

    # 12. Reimbursements - flag for manual review
    total_reimbursements = sum(
        data.reimbursements for data in payroll_by_store.values()
    )
    if total_reimbursements > Decimal("0.00"):
        warnings.append(
            {
                "type": "reimbursements_flagged",
                "message": f"Account 6152 has ${total_reimbursements} in reimbursements requiring manual allocation",
                "amount": str(total_reimbursements),
            }
        )

    # Set lines on journal entry
    jentry.Line = lines

    # Save the journal entry
    try:
        jentry.save(qb=qb.CLIENT)
        logger.info(
            "Saved journal entry",
            extra={
                "doc_number": doc_number,
                "year": year,
                "month": month,
                "line_count": len(lines),
                "stores": list(payroll_by_store.keys()),
            },
        )
    except Exception:
        logger.exception(
            "Failed to save journal entry",
            extra={"doc_number": doc_number, "year": year, "month": month},
        )
        raise

    # Generate QBO URL
    qbo_url = f"https://app.qbo.intuit.com/app/journal?txnId={jentry.Id}"

    return qbo_url, warnings


def process_payroll_allocation(
    year: int,
    month: int,
    gusto_csv_content: bytes,
    allow_update: bool = False,
) -> dict[str, Any]:
    """
    Process payroll allocation from Gusto CSV to QuickBooks journal entry.

    This is the main entry point for the Lambda handler.

    Args:
        year: The year (e.g., 2025)
        month: The month (1-12)
        gusto_csv_content: Raw bytes of the Gusto CSV file
        allow_update: If True, allow updating an existing entry. If False (default),
                      return an error if the entry already exists.

    Returns:
        Dictionary with results:
        - success: bool
        - journal_entry_url: str (if successful)
        - doc_number: str
        - summary: dict with allocation summary
        - warnings: list of any warnings
        - exists: bool (True if entry already exists and allow_update is False)
        - existing_url: str (URL to existing entry if exists is True)
    """
    doc_number = f"labor-{year}-{str(month).zfill(2)}"
    logger.info(
        "Starting payroll allocation",
        extra={
            "doc_number": doc_number,
            "year": year,
            "month": month,
            "allow_update": allow_update,
        },
    )

    try:
        # Parse Gusto CSV
        payroll_by_store = parse_gusto_csv(gusto_csv_content)

        if not payroll_by_store:
            logger.warning(
                "No payroll data found in CSV",
                extra={"doc_number": doc_number, "year": year, "month": month},
            )
            return {
                "success": False,
                "error": "No payroll data found in CSV",
            }

        logger.info(
            "Parsed Gusto CSV",
            extra={
                "doc_number": doc_number,
                "stores_found": list(payroll_by_store.keys()),
                "store_count": len(payroll_by_store),
            },
        )

        # Create journal entry
        qbo_url, warnings = create_payroll_allocation_journal(
            year, month, payroll_by_store, allow_update=allow_update
        )

        # Build summary
        summary = {
            "stores_processed": list(payroll_by_store.keys()),
            "total_gross_earnings": str(
                sum(d.gross_earnings for d in payroll_by_store.values())
            ),
            "total_employer_taxes": str(
                sum(d.employer_taxes for d in payroll_by_store.values())
            ),
        }

        logger.info(
            "Completed payroll allocation",
            extra={
                "doc_number": doc_number,
                "journal_entry_url": qbo_url,
                "summary": summary,
                "warning_count": len(warnings),
            },
        )

        return {
            "success": True,
            "journal_entry_url": qbo_url,
            "doc_number": doc_number,
            "summary": summary,
            "warnings": warnings,
        }

    except JournalEntryExistsError as e:
        logger.warning(
            "Journal entry already exists",
            extra={
                "doc_number": e.doc_number,
                "entry_id": e.entry_id,
                "entry_url": e.entry_url,
            },
        )
        return {
            "success": False,
            "exists": True,
            "doc_number": e.doc_number,
            "existing_url": e.entry_url,
            "error": f"Journal entry {e.doc_number} already exists. "
            "Check 'Replace existing entry' to update it.",
        }

    except Exception as e:
        logger.exception(
            "Error processing payroll allocation",
            extra={
                "doc_number": doc_number,
                "year": year,
                "month": month,
                "error": str(e),
            },
        )
        return {
            "success": False,
            "error": str(e),
        }


# For local testing / Phase 0 examination
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    print("Examining existing labor journal entries...")
    print("=" * 80)

    entries = examine_labor_journal_entries(count=3)

    for entry in entries:
        print(f"\nDocNumber: {entry['doc_number']}")
        print(f"TxnDate: {entry['txn_date']}")
        print(f"Lines: {len(entry['lines'])}")
        print("-" * 40)
        for line in entry["lines"]:
            dept = line["department"]
            acct = line["account"]
            posting = line["posting_type"]
            amount = line["amount"]
            desc = line["description"] or ""
            print(f"  {posting:6} | {acct:30} | {dept:15} | ${amount:>12} | {desc}")

    print("\n" + "=" * 80)
    print("JSON output for detailed analysis:")
    print(json.dumps(entries, indent=2, default=str))
