from _typeshed import Incomplete
from quickbooks.objects.detailline import DescriptionOnlyLine as DescriptionOnlyLine
from quickbooks.objects.detailline import DetailLine as DetailLine
from quickbooks.objects.detailline import DiscountLine as DiscountLine
from quickbooks.objects.detailline import SalesItemLine as SalesItemLine
from quickbooks.objects.detailline import SubtotalLine as SubtotalLine

from ..mixins import DeleteMixin as DeleteMixin
from .base import Address as Address
from .base import CustomerMemo as CustomerMemo
from .base import CustomField as CustomField
from .base import EmailAddress as EmailAddress
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .tax import TxnTaxDetail as TxnTaxDetail

class CreditMemo(
    DeleteMixin, QuickbooksTransactionEntity, QuickbooksManagedObject, LinkedTxnMixin
):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    RemainingCredit: int
    ExchangeRate: int
    DocNumber: str
    TxnDate: str
    PrivateNote: str
    TotalAmt: int
    ApplyTaxAfterDiscount: str
    PrintStatus: str
    EmailStatus: str
    Balance: int
    GlobalTaxCalculation: str
    BillAddr: Incomplete
    ShipAddr: Incomplete
    ClassRef: Incomplete
    DepartmentRef: Incomplete
    CustomerRef: Incomplete
    CurrencyRef: Incomplete
    CustomerMemo: Incomplete
    BillEmail: Incomplete
    TxnTaxDetail: Incomplete
    SalesTermRef: Incomplete
    CustomField: Incomplete
    Line: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self) -> Ref: ...
