from _typeshed import Incomplete
from quickbooks.objects.detailline import (
    AccountBasedExpenseLine as AccountBasedExpenseLine,
)
from quickbooks.objects.detailline import DetailLine as DetailLine
from quickbooks.objects.detailline import ItemBasedExpenseLine as ItemBasedExpenseLine
from quickbooks.objects.detailline import TDSLine as TDSLine

from ..mixins import DeleteMixin as DeleteMixin
from ..mixins import SendMixin as SendMixin
from .base import Address as Address
from .base import CustomField as CustomField
from .base import LinkedTxn as LinkedTxn
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .tax import TxnTaxDetail as TxnTaxDetail

class PurchaseOrder(
    DeleteMixin,
    QuickbooksManagedObject,
    QuickbooksTransactionEntity,
    LinkedTxnMixin,
    SendMixin,
):
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
