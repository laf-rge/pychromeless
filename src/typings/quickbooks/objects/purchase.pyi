from _typeshed import Incomplete
from quickbooks.objects.detailline import (
    AccountBasedExpenseLine as AccountBasedExpenseLine,
)
from quickbooks.objects.detailline import DetailLine as DetailLine
from quickbooks.objects.detailline import ItemBasedExpenseLine as ItemBasedExpenseLine
from quickbooks.objects.detailline import TDSLine as TDSLine

from ..mixins import DeleteMixin as DeleteMixin
from .base import Address as Address
from .base import LinkedTxn as LinkedTxn
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .tax import TxnTaxDetail as TxnTaxDetail

class Purchase(
    DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin
):
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
