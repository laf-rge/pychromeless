from ..mixins import DeleteMixin as DeleteMixin
from .base import Address as Address, LinkedTxn as LinkedTxn, LinkedTxnMixin as LinkedTxnMixin, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from .tax import TxnTaxDetail as TxnTaxDetail
from _typeshed import Incomplete
from quickbooks.objects.detailline import AccountBasedExpenseLine as AccountBasedExpenseLine, DetailLine as DetailLine, ItemBasedExpenseLine as ItemBasedExpenseLine, TDSLine as TDSLine

class Bill(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    DueDate: str | None
    Balance: int
    TotalAmt: str
    TxnDate: str
    DocNumber: str
    PrivateNote: str
    ExchangeRate: int
    GlobalTaxCalculation: Incomplete
    SalesTermRef: Incomplete
    CurrencyRef: Incomplete
    AttachableRef: Incomplete
    VendorRef: Ref
    DepartmentRef: Ref | None
    APAccountRef: Ref
    VendorAddr: Ref
    LinkedTxn: Incomplete
    Line: Incomplete
    def __init__(self) -> None: ...
    def to_linked_txn(self): ...
    def to_ref(self): ...
