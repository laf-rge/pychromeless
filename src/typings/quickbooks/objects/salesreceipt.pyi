from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from ..mixins import QuickbooksPdfDownloadable as QuickbooksPdfDownloadable
from ..mixins import VoidMixin as VoidMixin
from .base import Address as Address
from .base import CustomField as CustomField
from .base import EmailAddress as EmailAddress
from .base import LinkedTxn as LinkedTxn
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .detailline import DetailLine as DetailLine
from .tax import TxnTaxDetail as TxnTaxDetail

class SalesReceipt(
    DeleteMixin,
    QuickbooksPdfDownloadable,
    QuickbooksManagedObject,
    QuickbooksTransactionEntity,
    LinkedTxnMixin,
    VoidMixin,
):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    DocNumber: str
    TxnDate: str
    PrivateNote: str
    ShipDate: str
    TrackingNum: str
    TotalAmt: int
    PrintStatus: str
    EmailStatus: str
    Balance: int
    PaymentRefNum: str
    ApplyTaxAfterDiscount: bool
    ExchangeRate: int
    GlobalTaxCalculation: str
    CustomerMemo: Incomplete
    DeliveryInfo: Incomplete
    CreditCardPayment: Incomplete
    TxnSource: Incomplete
    DepartmentRef: Incomplete
    CurrencyRef: Incomplete
    TxnTaxDetail: Incomplete
    DepositToAccountRef: Incomplete
    BillAddr: Incomplete
    ShipAddr: Incomplete
    ShipMethodRef: Incomplete
    BillEmail: Incomplete
    CustomerRef: Incomplete
    ClassRef: Incomplete
    PaymentMethodRef: Incomplete
    CustomField: Incomplete
    Line: Incomplete
    LinkedTxn: Incomplete
    def __init__(self) -> None: ...
