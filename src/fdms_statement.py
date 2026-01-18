"""FDMS Statement PDF parsing and QuickBooks bill creation.

This module handles extracting billing data from FDMS credit card processor
statement PDFs and creating corresponding bills in QuickBooks.
"""

import io
import logging
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import pdfplumber

import qb
from decimal_utils import TWO_PLACES

logger = logging.getLogger(__name__)

# Account reference for all FDMS fee line items
FDMS_EXPENSE_ACCOUNT = 6210


@dataclass
class FDMSStatementData:
    """Parsed data from an FDMS statement PDF."""

    store_number: str
    statement_month: date  # Last day of statement month
    interchange_program_fees: Decimal
    service_charges: Decimal
    total_fees: Decimal
    chargebacks: list[dict[str, str]]
    adjustments: list[dict[str, str]]


class FDMSParseError(Exception):
    """Raised when PDF parsing fails."""

    pass


def parse_amount(amount_str: str) -> Decimal:
    """Parse amount string to positive Decimal.

    PDF shows negative amounts (e.g., -$607.65) but bills are positive expenses.
    """
    # Remove $ and commas, ignore negative sign
    cleaned = amount_str.replace("$", "").replace(",", "").replace("-", "").strip()
    return Decimal(cleaned).quantize(TWO_PLACES)


def parse_fdms_pdf(pdf_content: bytes) -> FDMSStatementData:
    """Parse FDMS statement PDF and extract billing data.

    Args:
        pdf_content: Raw bytes of the PDF file

    Returns:
        FDMSStatementData with extracted information

    Raises:
        FDMSParseError: If required data cannot be extracted
    """
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    if not text:
        raise FDMSParseError("Could not extract text from PDF")

    # Extract store number from header (e.g., "JERSEY MIKES 20407" or "JERSEY MIKE'S 20358")
    store_match = re.search(r"JERSEY MIKE'?S (\d{5})", text)
    if not store_match:
        raise FDMSParseError("Could not find store number in PDF")
    store_number = store_match.group(1)

    # Extract statement period end date
    # Format: "STATEMENT PERIOD: 12/01/25 - 12/31/25"
    period_match = re.search(
        r"STATEMENT PERIOD:\s*\d{2}/\d{2}/\d{2}\s*-\s*(\d{2})/(\d{2})/(\d{2})", text
    )
    if not period_match:
        raise FDMSParseError("Could not find statement period in PDF")
    month, day, year = period_match.groups()
    statement_date = date(2000 + int(year), int(month), int(day))

    # Extract fee totals - amounts shown as negative in PDF
    interchange_match = re.search(
        r"Total Interchange Charges/Program Fees\s*(-?\$?[\d,]+\.\d{2})", text
    )
    if not interchange_match:
        raise FDMSParseError("Could not find Total Interchange Charges/Program Fees")
    interchange_fees = parse_amount(interchange_match.group(1))

    service_match = re.search(r"Total Service Charges\s*(-?\$?[\d,]+\.\d{2})", text)
    if not service_match:
        raise FDMSParseError("Could not find Total Service Charges")
    service_charges = parse_amount(service_match.group(1))

    fees_match = re.search(r"Total Fees\s*(-?\$?[\d,]+\.\d{2})", text)
    if not fees_match:
        raise FDMSParseError("Could not find Total Fees")
    total_fees = parse_amount(fees_match.group(1))

    # Extract chargebacks
    chargebacks = _extract_chargebacks(text)

    # Extract adjustments
    adjustments = _extract_adjustments(text)

    return FDMSStatementData(
        store_number=store_number,
        statement_month=statement_date,
        interchange_program_fees=interchange_fees,
        service_charges=service_charges,
        total_fees=total_fees,
        chargebacks=chargebacks,
        adjustments=adjustments,
    )


def _extract_chargebacks(text: str) -> list[dict[str, str]]:
    """Extract chargeback information from PDF text."""
    chargebacks: list[dict[str, str]] = []

    # Find the CHARGEBACKS/REVERSALS section
    chargeback_section_match = re.search(
        r"CHARGEBACKS/REVERSALS\s+(.*?)(?=ADJUSTMENTS|SUMMARY OF CHARGES|$)",
        text,
        re.DOTALL,
    )

    if not chargeback_section_match:
        return chargebacks

    section_text = chargeback_section_match.group(1)

    # Check if there are no chargebacks
    if "No Chargebacks/Reversals for this Statement Period" in section_text:
        return chargebacks

    # Parse chargeback entries - format varies but typically includes:
    # date, reference number, description, card last 4, amount
    chargeback_pattern = re.compile(
        r"(\d{2}/\d{2}/\d{2})\s+"  # Date
        r"(\d+)\s+"  # Reference number
        r"(.+?)\s+"  # Description
        r"\*{4}(\d{4})\s+"  # Card last 4
        r"(-?\$?[\d,]+\.\d{2})",  # Amount
        re.MULTILINE,
    )

    for match in chargeback_pattern.finditer(section_text):
        chargebacks.append(
            {
                "date": match.group(1),
                "ref_no": match.group(2),
                "description": match.group(3).strip(),
                "card_last4": match.group(4),
                "amount": match.group(5),
            }
        )

    return chargebacks


def _extract_adjustments(text: str) -> list[dict[str, str]]:
    """Extract adjustment information from PDF text."""
    adjustments: list[dict[str, str]] = []

    # Find the ADJUSTMENTS section
    adjustments_section_match = re.search(
        r"ADJUSTMENTS\s+(.*?)(?=SUMMARY OF CHARGES|TOTAL DEPOSITS|$)",
        text,
        re.DOTALL,
    )

    if not adjustments_section_match:
        return adjustments

    section_text = adjustments_section_match.group(1)

    # Check if there are no adjustments
    if "No Adjustments for this Statement Period" in section_text:
        return adjustments

    # Parse adjustment entries
    adjustment_pattern = re.compile(
        r"(\d{2}/\d{2}/\d{2})\s+"  # Date
        r"(.+?)\s+"  # Description
        r"(-?\$?[\d,]+\.\d{2})",  # Amount
        re.MULTILINE,
    )

    for match in adjustment_pattern.finditer(section_text):
        adjustments.append(
            {
                "date": match.group(1),
                "description": match.group(2).strip(),
                "amount": match.group(3),
            }
        )

    return adjustments


def format_chargebacks_text(chargebacks: list[dict[str, str]]) -> str | None:
    """Format chargebacks list into readable text for notes."""
    if not chargebacks:
        return None

    lines = ["CHARGEBACKS:"]
    for cb in chargebacks:
        lines.append(
            f"- {cb['date']}: Ref#{cb['ref_no']} - {cb['description']} - "
            f"Card ****{cb['card_last4']} - {cb['amount']}"
        )
    return "\n".join(lines)


def format_adjustments_text(adjustments: list[dict[str, str]]) -> str | None:
    """Format adjustments list into readable text for notes."""
    if not adjustments:
        return None

    lines = ["ADJUSTMENTS:"]
    for adj in adjustments:
        lines.append(f"- {adj['date']}: {adj['description']} - {adj['amount']}")
    return "\n".join(lines)


def create_fdms_bills(
    data: FDMSStatementData,
) -> tuple[int, str | None, str | None]:
    """Create separate bills in QuickBooks for each FDMS fee type.

    Creates up to 3 bills per statement (one per fee type) so each can be
    matched with separate bank transactions.

    Args:
        data: Parsed FDMS statement data

    Returns:
        Tuple of (bills_created_count, chargebacks_text, adjustments_text)
    """
    from datetime import datetime

    from quickbooks.objects import Vendor

    # Get FDMS vendor
    qb.refresh_session()
    vendor_query = Vendor.filter(DisplayName="FDMS", qb=qb.CLIENT)
    if not vendor_query:
        logger.error("FDMS vendor not found in QuickBooks")
        raise ValueError("FDMS vendor not found in QuickBooks")
    supplier = vendor_query[0]

    # Base doc number format
    base_doc = f"FDMS-{data.store_number}-{data.statement_month.strftime('%Y%m')}"

    # Build private note (same for all bills from this statement)
    note_parts = [f"Generated by Josiah on {datetime.now().strftime('%Y-%m-%d')}"]

    chargebacks_text = format_chargebacks_text(data.chargebacks)
    adjustments_text = format_adjustments_text(data.adjustments)

    if chargebacks_text:
        note_parts.append("")
        note_parts.append(chargebacks_text)

    if adjustments_text:
        note_parts.append("")
        note_parts.append(adjustments_text)

    notes = "\n".join(note_parts)

    # Define the 3 fee types with their suffixes and amounts
    fee_types = [
        ("INT", "Interchange/Program Fees", data.interchange_program_fees),
        ("SVC", "Service Charges", data.service_charges),
        ("FEE", "Fees", data.total_fees),
    ]

    bills_created = 0

    for suffix, description, amount in fee_types:
        if amount <= 0:
            continue

        doc_number = f"{base_doc}-{suffix}"
        lines: list[list[Any]] = [
            [
                qb.wmc_account_ref(FDMS_EXPENSE_ACCOUNT),
                description,
                str(amount),
            ]
        ]

        try:
            qb.sync_bill(
                supplier=supplier,
                invoice_num=doc_number,
                invoice_date=data.statement_month,
                notes=notes,
                lines=lines,
                department=data.store_number,
            )
            bills_created += 1

            logger.info(
                "Created FDMS bill",
                extra={
                    "doc_number": doc_number,
                    "store": data.store_number,
                    "statement_month": str(data.statement_month),
                    "fee_type": suffix,
                    "amount": str(amount),
                },
            )

        except Exception:
            logger.exception(
                "Failed to create FDMS bill",
                extra={
                    "doc_number": doc_number,
                    "store": data.store_number,
                    "fee_type": suffix,
                },
            )
            raise

    return bills_created, chargebacks_text, adjustments_text
