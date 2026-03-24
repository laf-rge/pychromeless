"""BLS CES Monthly Report Processor.

Transforms a Gusto "BLS Report" CSV export into the data points required
for the Bureau of Labor Statistics Current Employment Statistics (CES)
Service-Providing One Pay Group form.

Usage:
    PYTHONPATH=src python src/bls_report.py <path_to_csv>
"""

import csv
import io
import sys
from decimal import Decimal

from decimal_utils import TWO_PLACES, ZERO

# Job titles classified as supervisory (all others are nonsupervisory)
SUPERVISORY_TITLES = {"Owner", "President"}

# Known nonsupervisory titles — if a title isn't in either set, we flag it
NONSUPERVISORY_TITLES = {"Crew", "Office"}

# Employment types that indicate salaried (hours should be excluded from BLS totals)
SALARIED_TYPES = {"Salary/No overtime", "Salary/Eligible for overtime"}


def parse_bls_csv(csv_path: str) -> list[dict[str, str]]:
    """Parse Gusto BLS Report CSV, skipping header preamble and totals rows.

    Args:
        csv_path: Path to the Gusto BLS Report CSV file.

    Returns:
        List of dicts, one per employee row.
    """
    with open(csv_path, encoding="utf-8") as f:
        content = f.read()

    # Skip preamble lines (report title, blank line, time period)
    # Find the header row that starts with "Payroll,"
    lines = content.split("\n")
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Payroll,"):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find CSV header row starting with 'Payroll,'")

    # Re-parse from the header row onward
    csv_content = "\n".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_content))

    rows = []
    for row in reader:
        payroll = row.get("Payroll", "")
        # Skip totals rows
        if "totals" in payroll.lower() or payroll.startswith("Grand"):
            continue
        # Skip empty rows
        if not payroll.strip():
            continue
        rows.append(row)

    return rows


def classify_title(title: str) -> str:
    """Classify a job title as supervisory or nonsupervisory.

    Args:
        title: The Primary job title from Gusto.

    Returns:
        "supervisory" or "nonsupervisory".

    Raises:
        ValueError: If the title is not in the known classification sets.
    """
    if title in SUPERVISORY_TITLES:
        return "supervisory"
    if title in NONSUPERVISORY_TITLES:
        return "nonsupervisory"
    raise ValueError(
        f"Unknown job title '{title}' — cannot classify. "
        "Add it to SUPERVISORY_TITLES or NONSUPERVISORY_TITLES."
    )


def is_salaried(employment_type: str) -> bool:
    """Check if an employee is salaried (hours excluded from BLS totals).

    Args:
        employment_type: The Employment type from Gusto.

    Returns:
        True if the employee is salaried.
    """
    return employment_type in SALARIED_TYPES


def compute_total_hours(row: dict[str, str]) -> Decimal:
    """Compute total hours for an employee row.

    Formula: Regular hours + Overtime hours + Double overtime hours + Total time off hours.
    Returns ZERO for salaried employees (hours excluded from BLS totals).

    Args:
        row: A single employee dict from the CSV.

    Returns:
        Total hours as Decimal.
    """
    if is_salaried(row["Employment type"]):
        return ZERO

    regular = Decimal(row["Regular hours"])
    overtime = Decimal(row["Overtime hours"])
    double_ot = Decimal(row["Double overtime hours"])
    time_off = Decimal(row["Total time off hours"])
    return regular + overtime + double_ot + time_off


def has_pay_activity(row: dict[str, str]) -> bool:
    """Check if an employee had pay activity (not a zero row).

    Args:
        row: A single employee dict from the CSV.

    Returns:
        True if the employee had non-zero gross earnings or hours.
    """
    gross = Decimal(row["Gross earnings"])
    total_hours = (
        Decimal(row["Regular hours"])
        + Decimal(row["Overtime hours"])
        + Decimal(row["Double overtime hours"])
        + Decimal(row["Total time off hours"])
    )
    return gross > ZERO or total_hours > ZERO


def process_bls_report(csv_path: str) -> dict:
    """Process a Gusto BLS Report CSV and compute BLS CES form values.

    Args:
        csv_path: Path to the Gusto BLS Report CSV file.

    Returns:
        Dict with computed BLS form values.
    """
    rows = parse_bls_csv(csv_path)

    # Extract pay period from first row
    first_payroll = rows[0]["Payroll"]
    # Format: "03/01/2026 - 03/15/2026, Regular"
    pay_period = first_payroll.split(",")[0].strip()

    # Filter to employees with pay activity
    active_rows = [r for r in rows if has_pay_activity(r)]

    # Classify each employee
    all_count = 0
    all_gross = ZERO
    all_hours = ZERO
    nonsup_count = 0
    nonsup_gross = ZERO
    nonsup_hours = ZERO

    for row in active_rows:
        title = row["Primary job title"]
        classification = classify_title(title)
        gross = Decimal(row["Gross earnings"])
        hours = compute_total_hours(row)

        all_count += 1
        all_gross += gross
        all_hours += hours

        if classification == "nonsupervisory":
            nonsup_count += 1
            nonsup_gross += gross
            nonsup_hours += hours

    return {
        "pay_period": pay_period,
        "total_employees": len(rows),
        "excluded_employees": len(rows) - len(active_rows),
        "all_employee_count": all_count,
        "all_gross_payroll": all_gross.quantize(TWO_PLACES),
        "all_total_hours": all_hours.quantize(TWO_PLACES),
        "nonsup_employee_count": nonsup_count,
        "nonsup_gross_payroll": nonsup_gross.quantize(TWO_PLACES),
        "nonsup_total_hours": nonsup_hours.quantize(TWO_PLACES),
        # TODO: Women employee count — needs separate Gusto report or lookup table
        "women_employee_count": None,
    }


def print_report(result: dict) -> None:
    """Print the BLS CES report in a readable format.

    Args:
        result: Dict returned by process_bls_report.
    """
    print(f"\nBLS CES Report — Pay Period: {result['pay_period']}")
    print("=" * 55)

    if result["excluded_employees"] > 0:
        print(
            f"  Note: {result['excluded_employees']} employee(s) excluded "
            "(no pay activity)"
        )
        print()

    print("ALL EMPLOYEES")
    print(f"  Count:          {result['all_employee_count']}")
    print(f"  Gross Payroll:  ${result['all_gross_payroll']:,.2f}")
    print(f"  Total Hours:    {result['all_total_hours']:,.2f}")
    print()

    print("NONSUPERVISORY EMPLOYEES")
    print(f"  Count:          {result['nonsup_employee_count']}")
    print(f"  Gross Payroll:  ${result['nonsup_gross_payroll']:,.2f}")
    print(f"  Total Hours:    {result['nonsup_total_hours']:,.2f}")
    print()

    if result["women_employee_count"] is None:
        print("WOMEN EMPLOYEES: [not available — needs gender data source]")
    else:
        print(f"WOMEN EMPLOYEES: {result['women_employee_count']}")
    print()


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_bls_report.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    result = process_bls_report(csv_path)
    print_report(result)


if __name__ == "__main__":
    main()
