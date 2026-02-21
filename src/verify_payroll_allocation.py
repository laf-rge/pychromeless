"""
Dry-run verification script for payroll allocation.

Compares what our new code would generate against the existing labor-2025-11 journal entry.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from payroll_allocation import (
    PAYROLL_ACCOUNTS,
    STORE_ORDER,
    PayrollData,
    get_journal_entry_by_doc_number,
    journal_entry_to_dict,
    parse_gusto_csv,
)
from qb import refresh_session


def load_gusto_csv(file_path: str) -> bytes:
    """Load and preprocess Gusto CSV file."""
    with open(file_path, "rb") as f:
        content = f.read()

    # The Gusto CSV has header lines before the actual data
    # Find the line that starts with "Payroll," which is the real header
    lines = content.decode("utf-8-sig").split("\n")
    for i, line in enumerate(lines):
        if line.startswith("Payroll,"):
            # Return from this line onwards
            return "\n".join(lines[i:]).encode("utf-8")

    return content


def generate_expected_lines(
    payroll_by_store: dict[str, PayrollData],
) -> dict[str, dict[str, Decimal]]:
    """
    Generate what our code would create as journal entry lines.

    Returns a dict mapping account_key -> store_id -> amount
    """
    result: dict[str, dict[str, Decimal]] = {}

    # Officer wages - use direct value from Gusto if available, else calculate
    officer_wages_by_store = {
        store: data.officer_wages
        for store, data in payroll_by_store.items()
        if data.officer_wages > Decimal("0")
    }
    total_officer_wages = sum(officer_wages_by_store.values())
    if total_officer_wages > Decimal("0"):
        result["officer_wages"] = officer_wages_by_store
    else:
        # Fallback: calculate from WMC gross - life_insurance
        wmc_data = payroll_by_store.get("WMC", PayrollData())
        officer_wages = wmc_data.gross_earnings - wmc_data.life_insurance
        if officer_wages > Decimal("0"):
            result["officer_wages"] = {"WMC": officer_wages}

    # Employer taxes
    result["employer_taxes"] = {
        store: data.employer_taxes
        for store, data in payroll_by_store.items()
        if data.employer_taxes > Decimal("0")
    }

    # Regular wages
    result["wages"] = {
        store: data.regular_earnings
        for store, data in payroll_by_store.items()
        if data.regular_earnings > Decimal("0")
    }

    # Overtime
    result["overtime"] = {
        store: data.overtime_earnings + data.double_overtime_earnings
        for store, data in payroll_by_store.items()
        if (data.overtime_earnings + data.double_overtime_earnings) > Decimal("0")
    }

    # Vacation (PTO + Holiday earnings)
    result["vacation_pay"] = {
        store: data.pto_earnings + data.holiday_earnings
        for store, data in payroll_by_store.items()
        if (data.pto_earnings + data.holiday_earnings) > Decimal("0")
    }

    # Sick
    result["sick_pay"] = {
        store: data.sick_earnings
        for store, data in payroll_by_store.items()
        if data.sick_earnings > Decimal("0")
    }

    # Meal period violations
    result["meal_violations"] = {
        store: data.meal_period_violations
        for store, data in payroll_by_store.items()
        if data.meal_period_violations > Decimal("0")
    }

    # Medical insurance
    result["medical_insurance"] = {
        store: data.medical_insurance + data.medical_insurance_dependents
        for store, data in payroll_by_store.items()
        if (data.medical_insurance + data.medical_insurance_dependents) > Decimal("0")
    }

    # Dental insurance
    result["dental_insurance"] = {
        store: data.dental_insurance + data.dental_insurance_dependents
        for store, data in payroll_by_store.items()
        if (data.dental_insurance + data.dental_insurance_dependents) > Decimal("0")
    }

    # HSA
    result["hsa"] = {
        store: data.hsa
        for store, data in payroll_by_store.items()
        if data.hsa > Decimal("0")
    }

    # Life insurance
    result["life_insurance"] = {
        store: data.life_insurance
        for store, data in payroll_by_store.items()
        if data.life_insurance > Decimal("0")
    }

    # Reimbursements (flagged)
    total_reimb = sum(d.reimbursements for d in payroll_by_store.values())
    if total_reimb > Decimal("0"):
        result["reimbursements_flagged"] = {"total": total_reimb}

    return result


def parse_existing_journal_entry(entry_data: dict) -> dict[str, dict[str, Decimal]]:
    """
    Parse existing journal entry lines into comparable format.

    Returns a dict mapping account_name -> department -> amount (debits only)
    """
    result: dict[str, dict[str, Decimal]] = {}

    for line in entry_data.get("lines", []):
        if line.get("posting_type") != "Debit":
            continue  # Skip credits, we only care about debits (store allocations)

        account = line.get("account", "")
        dept = line.get("department", "NOT SPECIFIED")
        amount = Decimal(line.get("amount", "0"))

        if account not in result:
            result[account] = {}

        # Map department names to store IDs
        dept_to_store = {
            "NOT SPECIFIED": "NOT_SPECIFIED",
            "WMC": "WMC",
            "20358 - Santa Rosa Ave": "20358",
            "20395 - Petaluma": "20395",
            "20400 - Hopper Ave": "20400",
            "20407 - Cotati": "20407",
        }
        store_id = dept_to_store.get(dept, dept)

        if store_id in result[account]:
            result[account][store_id] += amount
        else:
            result[account][store_id] = amount

    return result


def main() -> None:
    """Run dry-run verification."""
    print("=" * 80)
    print("PAYROLL ALLOCATION DRY-RUN VERIFICATION")
    print("Comparing generated output to existing labor-2025-11")
    print("=" * 80)

    # 1. Load and parse Gusto CSV
    csv_path = (
        Path.home()
        / "Downloads"
        / "Wagoner-Management-Corp-Total-By-Location-2025-11-01-to-2025-11-30-3.csv"
    )
    print(f"\n1. Loading Gusto CSV from: {csv_path}")

    csv_content = load_gusto_csv(str(csv_path))
    payroll_by_store = parse_gusto_csv(csv_content)

    print(f"   Parsed {len(payroll_by_store)} stores:")
    for store_id in STORE_ORDER:
        if store_id in payroll_by_store:
            data = payroll_by_store[store_id]
            print(
                f"   - {store_id}: gross=${data.gross_earnings}, taxes=${data.employer_taxes}"
            )

    # 2. Generate what our code would create
    print("\n2. Generating expected journal entry lines...")
    generated = generate_expected_lines(payroll_by_store)

    # 3. Retrieve existing journal entry
    print("\n3. Retrieving existing labor-2025-11 from QuickBooks...")
    refresh_session()
    existing_entry = get_journal_entry_by_doc_number("labor-2025-11")

    if not existing_entry:
        print("   ERROR: Could not find labor-2025-11 in QuickBooks")
        return

    existing_data = journal_entry_to_dict(existing_entry)
    print(f"   Found: ID={existing_data['id']}, Date={existing_data['txn_date']}")

    existing_parsed = parse_existing_journal_entry(existing_data)

    # 4. Compare
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)

    # Map our account keys to QBO account names (full path)
    account_key_to_name = {
        "officer_wages": "Payroll Expenses Labor:Officer Wages",
        "employer_taxes": "Payroll Expenses Labor:Payroll Taxes - Employer",
        "wages": "Payroll Expenses Labor:Payroll Expenses - Hourly:Wages",
        "overtime": "Payroll Expenses Labor:Payroll Expenses - Hourly:Overtime",
        "vacation_pay": "Payroll Expenses Labor:Payroll Expenses - Hourly:Vacation Pay",
        "sick_pay": "Payroll Expenses Labor:Payroll Expenses - Hourly:Sick Pay",
        "meal_violations": "Payroll Expenses Labor:Payroll Expenses - Hourly:Meal period violations",
        "medical_insurance": "Payroll Expenses Labor:Employee Benefits Contributions:Medical Insurance",
        "dental_insurance": "Payroll Expenses Labor:Employee Benefits Contributions:Dental Insurance",
        "hsa": "Payroll Expenses Labor:Employee Benefits Contributions:HSA",
        "life_insurance": "Payroll Expenses Labor:Employee Benefits Contributions:Life Insurance",
    }

    for account_key, account_name in account_key_to_name.items():
        gen_data = generated.get(account_key, {})
        existing_acct_data = existing_parsed.get(account_name, {})

        if not gen_data and not existing_acct_data:
            continue

        print(f"\n{account_name} ({PAYROLL_ACCOUNTS.get(account_key, '?')}):")

        # Get all stores from both
        all_stores = set(gen_data.keys()) | set(existing_acct_data.keys())

        for store in STORE_ORDER:
            if store not in all_stores:
                continue
            gen_amt = gen_data.get(store, Decimal("0"))
            exist_amt = existing_acct_data.get(store, Decimal("0"))
            diff = gen_amt - exist_amt

            status = "✓" if abs(diff) < Decimal("0.01") else "✗"
            if diff != Decimal("0"):
                print(
                    f"  {status} {store}: Generated=${gen_amt:.2f}, Existing=${exist_amt:.2f}, Diff=${diff:.2f}"
                )
            else:
                print(f"  {status} {store}: ${gen_amt:.2f}")

    # Show accounts in existing that we don't generate
    print("\n" + "-" * 80)
    print("ACCOUNTS IN EXISTING JE NOT IN OUR GENERATION:")
    print("-" * 80)

    our_account_names = set(account_key_to_name.values())
    for account_name, store_data in existing_parsed.items():
        if account_name not in our_account_names:
            total = sum(store_data.values())
            print(f"\n{account_name}: ${total:.2f}")
            for store, amt in store_data.items():
                print(f"  - {store}: ${amt:.2f}")

    # Show flagged items
    print("\n" + "-" * 80)
    print("FLAGGED FOR MANUAL REVIEW:")
    print("-" * 80)
    if "reimbursements_flagged" in generated:
        print(
            f"Total reimbursements: ${generated['reimbursements_flagged']['total']:.2f}"
        )


if __name__ == "__main__":
    main()
