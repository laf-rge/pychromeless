"""Unit tests for payroll_allocation module."""

import sys
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Mock quickbooks module before importing payroll_allocation
sys.modules["quickbooks"] = MagicMock()
sys.modules["quickbooks.helpers"] = MagicMock()
sys.modules["quickbooks.objects"] = MagicMock()
sys.modules["quickbooks.objects.journalentry"] = MagicMock()

# Mock qb module
mock_qb = MagicMock()
mock_qb.TWO_PLACES = Decimal(10) ** -2
mock_qb.refresh_session = MagicMock()
mock_qb.wmc_account_ref = MagicMock()
mock_qb.CLIENT = MagicMock()
sys.modules["qb"] = mock_qb

from payroll_allocation import (
    PAYROLL_ACCOUNTS,
    STORE_ADDRESS_MAP,
    STORE_ORDER,
    PayrollData,
    parse_gusto_csv,
)


class TestPayrollData(unittest.TestCase):
    """Tests for PayrollData dataclass."""

    def test_payroll_data_defaults(self) -> None:
        """Test that PayrollData initializes with zero defaults."""
        data = PayrollData()
        self.assertEqual(data.gross_earnings, Decimal("0.00"))
        self.assertEqual(data.employer_taxes, Decimal("0.00"))
        self.assertEqual(data.regular_earnings, Decimal("0.00"))
        self.assertEqual(data.overtime_earnings, Decimal("0.00"))
        self.assertEqual(data.reimbursements, Decimal("0.00"))

    def test_payroll_data_add(self) -> None:
        """Test adding two PayrollData instances."""
        data1 = PayrollData(
            gross_earnings=Decimal("1000.00"),
            employer_taxes=Decimal("100.00"),
            regular_earnings=Decimal("900.00"),
            overtime_earnings=Decimal("100.00"),
        )
        data2 = PayrollData(
            gross_earnings=Decimal("500.00"),
            employer_taxes=Decimal("50.00"),
            regular_earnings=Decimal("400.00"),
            overtime_earnings=Decimal("100.00"),
        )

        data1.add(data2)

        self.assertEqual(data1.gross_earnings, Decimal("1500.00"))
        self.assertEqual(data1.employer_taxes, Decimal("150.00"))
        self.assertEqual(data1.regular_earnings, Decimal("1300.00"))
        self.assertEqual(data1.overtime_earnings, Decimal("200.00"))


class TestStoreMapping(unittest.TestCase):
    """Tests for store address mapping."""

    def test_store_address_map_contains_expected_zips(self) -> None:
        """Test that all expected zip codes are in the mapping."""
        expected_zips = ["94954", "95407", "95403", "94931", "94928"]
        for zip_code in expected_zips:
            self.assertIn(zip_code, STORE_ADDRESS_MAP)

    def test_store_address_map_values(self) -> None:
        """Test that zip codes map to correct store IDs."""
        self.assertEqual(STORE_ADDRESS_MAP["94954"], "20395")  # Petaluma
        self.assertEqual(STORE_ADDRESS_MAP["95407"], "20358")  # Santa Rosa Ave
        self.assertEqual(STORE_ADDRESS_MAP["95403"], "20400")  # Hopper Ave
        self.assertEqual(STORE_ADDRESS_MAP["94931"], "20407")  # Cotati
        self.assertEqual(STORE_ADDRESS_MAP["94928"], "WMC")  # Central Office

    def test_store_order_contains_all_stores(self) -> None:
        """Test that STORE_ORDER contains all store IDs."""
        expected_stores = ["WMC", "20358", "20395", "20400", "20407"]
        for store in expected_stores:
            self.assertIn(store, STORE_ORDER)


class TestPayrollAccounts(unittest.TestCase):
    """Tests for payroll account configuration."""

    def test_payroll_accounts_contain_expected_keys(self) -> None:
        """Test that all expected account types are defined."""
        expected_keys = [
            "officer_wages",
            "employer_taxes",
            "wages",
            "overtime",
            "vacation_pay",
            "sick_pay",
            "medical_insurance",
            "dental_insurance",
            "hsa",
            "life_insurance",
        ]
        for key in expected_keys:
            self.assertIn(key, PAYROLL_ACCOUNTS)

    def test_payroll_accounts_are_strings(self) -> None:
        """Test that all account numbers are strings."""
        for key, value in PAYROLL_ACCOUNTS.items():
            self.assertIsInstance(value, str, f"{key} should be a string")


class TestParseGustoCsv(unittest.TestCase):
    """Tests for parse_gusto_csv function."""

    def test_parse_empty_csv(self) -> None:
        """Test parsing empty CSV returns empty dict."""
        csv_content = b"Work address (zip)\n"
        result = parse_gusto_csv(csv_content)
        self.assertEqual(result, {})

    def test_parse_csv_with_valid_data(self) -> None:
        """Test parsing CSV with valid employee data."""
        csv_content = b"""Payroll,Work address (zip),Gross earnings,Total employer taxes,Regular earnings,Overtime earnings,Double overtime earnings,Paid time off earnings,Sick time off earnings,Total reimbursements,Officer Wages,Meal Period Violations
Nov 15 - 30,94954,1000.00,100.00,900.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00
Nov 15 - 30,94954,500.00,50.00,450.00,50.00,0.00,0.00,0.00,0.00,0.00,0.00
"""
        result = parse_gusto_csv(csv_content)

        self.assertIn("20395", result)  # Petaluma store
        self.assertEqual(result["20395"].gross_earnings, Decimal("1500.00"))
        self.assertEqual(result["20395"].employer_taxes, Decimal("150.00"))
        self.assertEqual(result["20395"].regular_earnings, Decimal("1350.00"))
        self.assertEqual(result["20395"].overtime_earnings, Decimal("150.00"))

    def test_parse_csv_multiple_stores(self) -> None:
        """Test parsing CSV with employees at different stores."""
        csv_content = b"""Payroll,Work address (zip),Gross earnings,Total employer taxes,Regular earnings,Overtime earnings,Double overtime earnings,Paid time off earnings,Sick time off earnings,Total reimbursements,Officer Wages,Meal Period Violations
Nov 15 - 30,94954,1000.00,100.00,900.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00
Nov 15 - 30,95407,800.00,80.00,750.00,50.00,0.00,0.00,0.00,0.00,0.00,0.00
Nov 15 - 30,94928,5000.00,500.00,0.00,0.00,0.00,0.00,0.00,0.00,5000.00,0.00
"""
        result = parse_gusto_csv(csv_content)

        self.assertIn("20395", result)  # Petaluma
        self.assertIn("20358", result)  # Santa Rosa Ave
        self.assertIn("WMC", result)  # Central Office

        self.assertEqual(result["20395"].gross_earnings, Decimal("1000.00"))
        self.assertEqual(result["20358"].gross_earnings, Decimal("800.00"))
        self.assertEqual(result["WMC"].gross_earnings, Decimal("5000.00"))

    def test_parse_csv_skips_grand_totals(self) -> None:
        """Test that Grand totals row is skipped."""
        csv_content = b"""Payroll,Work address (zip),Gross earnings,Total employer taxes,Regular earnings,Overtime earnings,Double overtime earnings,Paid time off earnings,Sick time off earnings,Total reimbursements,Officer Wages,Meal Period Violations
Nov 15 - 30,94954,1000.00,100.00,900.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00
Grand totals,,,50000.00,5000.00,45000.00,5000.00,0.00,0.00,0.00,0.00,0.00,0.00
"""
        result = parse_gusto_csv(csv_content)

        self.assertEqual(len(result), 1)
        self.assertIn("20395", result)
        self.assertEqual(result["20395"].gross_earnings, Decimal("1000.00"))

    def test_parse_csv_with_unknown_zip(self) -> None:
        """Test that unknown zip codes are skipped with warning."""
        csv_content = b"""Payroll,Work address (zip),Gross earnings,Total employer taxes,Regular earnings,Overtime earnings,Double overtime earnings,Paid time off earnings,Sick time off earnings,Total reimbursements,Officer Wages,Meal Period Violations
Nov 15 - 30,94954,1000.00,100.00,900.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00
Nov 15 - 30,99999,500.00,50.00,450.00,50.00,0.00,0.00,0.00,0.00,0.00,0.00
"""
        result = parse_gusto_csv(csv_content)

        # Only known zip should be in result
        self.assertEqual(len(result), 1)
        self.assertIn("20395", result)
        self.assertNotIn("99999", result)

    def test_parse_csv_with_bom(self) -> None:
        """Test parsing CSV with UTF-8 BOM."""
        # UTF-8 BOM is handled by utf-8-sig encoding
        csv_content = b"\xef\xbb\xbfPayroll,Work address (zip),Gross earnings,Total employer taxes,Regular earnings,Overtime earnings,Double overtime earnings,Paid time off earnings,Sick time off earnings,Total reimbursements,Officer Wages,Meal Period Violations\nNov 15 - 30,94954,1000.00,100.00,900.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00\n"
        result = parse_gusto_csv(csv_content)

        self.assertIn("20395", result)
        self.assertEqual(result["20395"].gross_earnings, Decimal("1000.00"))

    def test_parse_csv_with_empty_values(self) -> None:
        """Test parsing CSV with empty/missing values."""
        csv_content = b"""Payroll,Work address (zip),Gross earnings,Total employer taxes,Regular earnings,Overtime earnings,Double overtime earnings,Paid time off earnings,Sick time off earnings,Total reimbursements,Officer Wages,Meal Period Violations
Nov 15 - 30,94954,1000.00,100.00,,,,,,,,
"""
        result = parse_gusto_csv(csv_content)

        self.assertIn("20395", result)
        self.assertEqual(result["20395"].gross_earnings, Decimal("1000.00"))
        self.assertEqual(result["20395"].regular_earnings, Decimal("0.00"))


class TestCreatePayrollAllocationJournal(unittest.TestCase):
    """Tests for create_payroll_allocation_journal function."""

    @patch("payroll_allocation.refresh_session")
    @patch("payroll_allocation.qb")
    @patch("payroll_allocation.get_store_refs")
    @patch("payroll_allocation.get_journal_entry_by_doc_number")
    @patch("payroll_allocation.wmc_account_ref")
    def test_create_journal_entry_success(
        self,
        mock_account_ref: MagicMock,
        mock_get_entry: MagicMock,
        mock_store_refs: MagicMock,
        mock_qb: MagicMock,
        mock_refresh: MagicMock,
    ) -> None:
        """Test successful journal entry creation."""
        from payroll_allocation import create_payroll_allocation_journal

        # Setup mocks
        mock_get_entry.return_value = None
        mock_store_refs.return_value = {
            "WMC": MagicMock(),
            "20358": MagicMock(),
            "20395": MagicMock(),
            "20400": MagicMock(),
            "20407": MagicMock(),
        }
        mock_account_ref.return_value = MagicMock()

        # Mock the JournalEntry save
        mock_entry = MagicMock()
        mock_entry.Id = "123"

        with patch("payroll_allocation.JournalEntry") as MockJournalEntry:
            MockJournalEntry.return_value = mock_entry

            payroll_data = {
                "20395": PayrollData(
                    gross_earnings=Decimal("1000.00"),
                    employer_taxes=Decimal("100.00"),
                    regular_earnings=Decimal("900.00"),
                ),
            }

            url, warnings = create_payroll_allocation_journal(2025, 11, payroll_data)

            self.assertIn("123", url)
            self.assertEqual(warnings, [])
            mock_entry.save.assert_called_once()

    @patch("payroll_allocation.refresh_session")
    @patch("payroll_allocation.qb")
    @patch("payroll_allocation.get_store_refs")
    @patch("payroll_allocation.get_journal_entry_by_doc_number")
    @patch("payroll_allocation.wmc_account_ref")
    def test_create_journal_entry_with_reimbursements(
        self,
        mock_account_ref: MagicMock,
        mock_get_entry: MagicMock,
        mock_store_refs: MagicMock,
        mock_qb: MagicMock,
        mock_refresh: MagicMock,
    ) -> None:
        """Test that reimbursements trigger a warning."""
        from payroll_allocation import create_payroll_allocation_journal

        mock_get_entry.return_value = None
        mock_store_refs.return_value = {
            "WMC": MagicMock(),
            "20358": MagicMock(),
            "20395": MagicMock(),
            "20400": MagicMock(),
            "20407": MagicMock(),
        }
        mock_account_ref.return_value = MagicMock()

        mock_entry = MagicMock()
        mock_entry.Id = "123"

        with patch("payroll_allocation.JournalEntry") as MockJournalEntry:
            MockJournalEntry.return_value = mock_entry

            payroll_data = {
                "20395": PayrollData(
                    gross_earnings=Decimal("1000.00"),
                    reimbursements=Decimal("250.00"),
                ),
            }

            url, warnings = create_payroll_allocation_journal(2025, 11, payroll_data)

            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["type"], "reimbursements_flagged")
            self.assertIn("250.00", warnings[0]["message"])

    @patch("payroll_allocation.refresh_session")
    @patch("payroll_allocation.get_journal_entry_by_doc_number")
    def test_create_journal_entry_exists_error(
        self,
        mock_get_entry: MagicMock,
        mock_refresh: MagicMock,
    ) -> None:
        """Test that JournalEntryExistsError is raised when entry exists."""
        from payroll_allocation import (
            JournalEntryExistsError,
            create_payroll_allocation_journal,
        )

        # Mock an existing entry
        mock_existing = MagicMock()
        mock_existing.Id = "999"
        mock_get_entry.return_value = mock_existing

        payroll_data = {
            "20395": PayrollData(
                gross_earnings=Decimal("1000.00"),
            ),
        }

        with self.assertRaises(JournalEntryExistsError) as context:
            create_payroll_allocation_journal(
                2025, 11, payroll_data, allow_update=False
            )

        self.assertEqual(context.exception.doc_number, "labor-2025-11")
        self.assertEqual(context.exception.entry_id, "999")
        self.assertIn("999", context.exception.entry_url)

    @patch("payroll_allocation.refresh_session")
    @patch("payroll_allocation.qb")
    @patch("payroll_allocation.get_store_refs")
    @patch("payroll_allocation.get_journal_entry_by_doc_number")
    @patch("payroll_allocation.wmc_account_ref")
    def test_create_journal_entry_allow_update(
        self,
        mock_account_ref: MagicMock,
        mock_get_entry: MagicMock,
        mock_store_refs: MagicMock,
        mock_qb: MagicMock,
        mock_refresh: MagicMock,
    ) -> None:
        """Test that existing entry is updated when allow_update is True."""
        from payroll_allocation import create_payroll_allocation_journal

        # Mock an existing entry
        mock_existing = MagicMock()
        mock_existing.Id = "999"
        mock_existing.Line = [MagicMock()]  # Has existing lines
        mock_get_entry.return_value = mock_existing

        mock_store_refs.return_value = {
            "WMC": MagicMock(),
            "20358": MagicMock(),
            "20395": MagicMock(),
            "20400": MagicMock(),
            "20407": MagicMock(),
        }
        mock_account_ref.return_value = MagicMock()

        payroll_data = {
            "20395": PayrollData(
                gross_earnings=Decimal("1000.00"),
                employer_taxes=Decimal("100.00"),
                regular_earnings=Decimal("900.00"),
            ),
        }

        url, warnings = create_payroll_allocation_journal(
            2025, 11, payroll_data, allow_update=True
        )

        self.assertIn("999", url)
        mock_existing.save.assert_called_once()


class TestProcessPayrollAllocation(unittest.TestCase):
    """Tests for process_payroll_allocation function."""

    @patch("payroll_allocation.create_payroll_allocation_journal")
    def test_process_success(self, mock_create: MagicMock) -> None:
        """Test successful end-to-end processing."""
        from payroll_allocation import process_payroll_allocation

        mock_create.return_value = (
            "https://app.qbo.intuit.com/app/journal?txnId=123",
            [],
        )

        csv_content = b"""Payroll,Work address (zip),Gross earnings,Total employer taxes,Regular earnings,Overtime earnings,Double overtime earnings,Paid time off earnings,Sick time off earnings,Total reimbursements,Officer Wages,Meal Period Violations
Nov 15 - 30,94954,1000.00,100.00,900.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00
"""

        result = process_payroll_allocation(2025, 11, csv_content)

        self.assertTrue(result["success"])
        self.assertEqual(result["doc_number"], "labor-2025-11")
        self.assertIn("journal_entry_url", result)
        self.assertEqual(result["warnings"], [])

    def test_process_empty_csv(self) -> None:
        """Test processing empty CSV returns error."""
        from payroll_allocation import process_payroll_allocation

        csv_content = b"Work address (zip)\n"

        result = process_payroll_allocation(2025, 11, csv_content)

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("payroll_allocation.create_payroll_allocation_journal")
    def test_process_entry_exists(self, mock_create: MagicMock) -> None:
        """Test that existing entry returns exists error."""
        from payroll_allocation import (
            JournalEntryExistsError,
            process_payroll_allocation,
        )

        mock_create.side_effect = JournalEntryExistsError(
            "labor-2025-11",
            "999",
            "https://app.qbo.intuit.com/app/journal?txnId=999",
        )

        csv_content = b"""Payroll,Work address (zip),Gross earnings,Total employer taxes,Regular earnings,Overtime earnings,Double overtime earnings,Paid time off earnings,Sick time off earnings,Total reimbursements,Officer Wages,Meal Period Violations
Nov 15 - 30,94954,1000.00,100.00,900.00,100.00,0.00,0.00,0.00,0.00,0.00,0.00
"""

        result = process_payroll_allocation(2025, 11, csv_content)

        self.assertFalse(result["success"])
        self.assertTrue(result["exists"])
        self.assertEqual(result["doc_number"], "labor-2025-11")
        self.assertIn("999", result["existing_url"])
        self.assertIn("already exists", result["error"])


if __name__ == "__main__":
    unittest.main()
