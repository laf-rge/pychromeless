from enum import StrEnum


class OperationType(StrEnum):
    DAILY_SALES = "daily_sales"
    INVOICE_SYNC = "invoice_sync"
    EMAIL_TIPS = "email_tips"
    UPDATE_FOOD_HANDLER_PDFS = "update_food_handler_pdfs"
    DAILY_JOURNAL = "daily_journal"
    THIRD_PARTY_DEPOSIT = "third_party_deposit"
    PAYROLL_ALLOCATION = "payroll_allocation"
    GRUBHUB_CSV_IMPORT = "grubhub_csv_import"
    FDMS_STATEMENT_IMPORT = "fdms_statement_import"

    @property
    def display_name(self) -> str:
        """Human-readable name for the operation"""
        display_names = {
            OperationType.DAILY_SALES: "Daily Sales Processing",
            OperationType.INVOICE_SYNC: "Invoice Synchronization",
            OperationType.EMAIL_TIPS: "Tips Email Generation",
            OperationType.UPDATE_FOOD_HANDLER_PDFS: "Food Handler PDF Update",
            OperationType.DAILY_JOURNAL: "Daily Journal Processing",
            OperationType.THIRD_PARTY_DEPOSIT: "Third Party Deposits",
            OperationType.PAYROLL_ALLOCATION: "Payroll Allocation",
            OperationType.GRUBHUB_CSV_IMPORT: "GrubHub CSV Import",
            OperationType.FDMS_STATEMENT_IMPORT: "FDMS Statement Import",
        }
        return display_names.get(self, self.value.replace("_", " ").title())

    @property
    def ttl_seconds(self) -> int:
        """Get TTL in seconds based on operation type"""
        ttl_periods = {
            OperationType.DAILY_SALES: 24 * 60 * 60,  # 24 hours
            OperationType.INVOICE_SYNC: 48 * 60 * 60,  # 48 hours
            OperationType.EMAIL_TIPS: 12 * 60 * 60,  # 12 hours
            OperationType.UPDATE_FOOD_HANDLER_PDFS: 12 * 60 * 60,  # 12 hours
            OperationType.DAILY_JOURNAL: 24 * 60 * 60,  # 24 hours
            OperationType.THIRD_PARTY_DEPOSIT: 24 * 60 * 60,  # 24 hours
            OperationType.PAYROLL_ALLOCATION: 24 * 60 * 60,  # 24 hours
            OperationType.GRUBHUB_CSV_IMPORT: 24 * 60 * 60,  # 24 hours
            OperationType.FDMS_STATEMENT_IMPORT: 24 * 60 * 60,  # 24 hours
        }
        return ttl_periods.get(self, 24 * 60 * 60)  # Default to 24 hours
