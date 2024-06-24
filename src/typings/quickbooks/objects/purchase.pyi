from ..mixins import DeleteMixin as DeleteMixin
from .base import Address as Address, LinkedTxn as LinkedTxn, LinkedTxnMixin as LinkedTxnMixin, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from .tax import TxnTaxDetail as TxnTaxDetail
from _typeshed import Incomplete
from quickbooks.objects.detailline import AccountBasedExpenseLine as AccountBasedExpenseLine, DetailLine as DetailLine, ItemBasedExpenseLine as ItemBasedExpenseLine, TDSLine as TDSLine

class Purchase(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    DocNumber: str
    TxnDate: str
    ExchangeRate: int
    PrivateNote: str
    PaymentType: str
    Credit: bool
    TotalAmt: int
    PrintStatus: str
    PurchaseEx: Incomplete
    TxnSource: Incomplete
    GlobalTaxCalculation: str
    TxnTaxDetail: Incomplete
    DepartmentRef: Incomplete
    AccountRef: Incomplete
    EntityRef: Incomplete
    CurrencyRef: Incomplete
    PaymentMethodRef: Incomplete
    RemitToAddr: Incomplete
    Line: Incomplete
    LinkedTxn: Incomplete
    def __init__(self) -> None: ...
