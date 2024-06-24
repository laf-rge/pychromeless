from ..mixins import DeleteNoIdMixin as DeleteNoIdMixin, ListMixin as ListMixin, ReadMixin as ReadMixin, UpdateNoIdMixin as UpdateNoIdMixin
from .base import QuickbooksBaseObject as QuickbooksBaseObject, Ref as Ref
from .bill import Bill as Bill
from .creditmemo import CreditMemo as CreditMemo
from .deposit import Deposit as Deposit
from .estimate import Estimate as Estimate
from .invoice import Invoice as Invoice
from .journalentry import JournalEntry as JournalEntry
from .purchase import Purchase as Purchase
from .purchaseorder import PurchaseOrder as PurchaseOrder
from .refundreceipt import RefundReceipt as RefundReceipt
from .salesreceipt import SalesReceipt as SalesReceipt
from .transfer import Transfer as Transfer
from .vendorcredit import VendorCredit as VendorCredit
from _typeshed import Incomplete

class ScheduleInfo(QuickbooksBaseObject):
    StartDate: Incomplete
    EndDate: Incomplete
    DaysBefore: Incomplete
    MaxOccurrences: Incomplete
    RemindDays: Incomplete
    IntervalType: Incomplete
    NumInterval: Incomplete
    DayOfMonth: Incomplete
    DayOfWeek: Incomplete
    MonthOfYear: Incomplete
    WeekOfMonth: Incomplete
    NextDate: Incomplete
    PreviousDate: Incomplete
    def __init__(self) -> None: ...

class RecurringInfo(QuickbooksBaseObject):
    class_dict: Incomplete
    qbo_object_name: str
    RecurType: str
    Name: str
    Active: bool
    def __init__(self) -> None: ...

class Recurring:
    class_dict: Incomplete

class RecurringBill(Bill):
    class_dict: Incomplete

class RecurringPurchase(Purchase):
    class_dict: Incomplete

class RecurringCreditMemo(CreditMemo):
    class_dict: Incomplete

class RecurringDeposit(Deposit):
    class_dict: Incomplete

class RecurringEstimate(Estimate):
    class_dict: Incomplete

class RecurringInvoice(Invoice):
    class_dict: Incomplete

class RecurringJournalEntry(JournalEntry):
    class_dict: Incomplete

class RecurringRefundReceipt(RefundReceipt):
    class_dict: Incomplete

class RecurringSalesReceipt(SalesReceipt):
    class_dict: Incomplete

class RecurringTransfer(Transfer):
    class_dict: Incomplete

class RecurringVendorCredit(VendorCredit):
    class_dict: Incomplete

class RecurringPurchaseOrder(PurchaseOrder):
    class_dict: Incomplete

class RecurringTransaction(QuickbooksBaseObject, ReadMixin, UpdateNoIdMixin, ListMixin, DeleteNoIdMixin):
    class_dict: Incomplete
    qbo_object_name: str
