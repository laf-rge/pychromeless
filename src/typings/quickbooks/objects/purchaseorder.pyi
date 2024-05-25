from ..mixins import DeleteMixin as DeleteMixin, SendMixin as SendMixin
from .base import Address as Address, CustomField as CustomField, LinkedTxn as LinkedTxn, LinkedTxnMixin as LinkedTxnMixin, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from .tax import TxnTaxDetail as TxnTaxDetail
from _typeshed import Incomplete
from quickbooks.objects.detailline import AccountBasedExpenseLine as AccountBasedExpenseLine, DetailLine as DetailLine, ItemBasedExpenseLine as ItemBasedExpenseLine, TDSLine as TDSLine

class PurchaseOrder(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin, SendMixin):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    POStatus: Incomplete
    DocNumber: Incomplete
    TxnDate: Incomplete
    PrivateNote: Incomplete
    TotalAmt: int
    DueDate: Incomplete
    ExchangeRate: int
    GlobalTaxCalculation: str
    Memo: Incomplete
    ShipMethodRef: Incomplete
    TxnTaxDetail: Incomplete
    VendorAddr: Incomplete
    ShipAddr: Incomplete
    VendorRef: Incomplete
    APAccountRef: Incomplete
    AttachableRef: Incomplete
    ClassRef: Incomplete
    SalesTermRef: Incomplete
    TaxCodeRef: Incomplete
    CurrencyRef: Incomplete
    Line: Incomplete
    CustomField: Incomplete
    LinkedTxn: Incomplete
    def __init__(self) -> None: ...
