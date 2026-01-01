from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from ..mixins import QuickbooksPdfDownloadable as QuickbooksPdfDownloadable
from ..mixins import SendMixin as SendMixin
from ..mixins import VoidMixin as VoidMixin
from .base import Address as Address
from .base import CustomerMemo as CustomerMemo
from .base import CustomField as CustomField
from .base import EmailAddress as EmailAddress
from .base import LinkedTxn as LinkedTxn
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import MetaData as MetaData
from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .detailline import DescriptionOnlyLine as DescriptionOnlyLine
from .detailline import DetailLine as DetailLine
from .detailline import DiscountLine as DiscountLine
from .detailline import GroupLine as GroupLine
from .detailline import SalesItemLine as SalesItemLine
from .detailline import SubtotalLine as SubtotalLine
from .tax import TxnTaxDetail as TxnTaxDetail

class DeliveryInfo(QuickbooksBaseObject):
    DeliveryType: str
    DeliveryTime: str
    def __init__(self) -> None: ...

class Invoice(
    DeleteMixin,
    QuickbooksPdfDownloadable,
    QuickbooksManagedObject,
    QuickbooksTransactionEntity,
    LinkedTxnMixin,
    SendMixin,
    VoidMixin,
):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    Deposit: int
    Balance: int
    AllowIPNPayment: bool
    AllowOnlineCreditCardPayment: bool
    AllowOnlineACHPayment: bool
    DocNumber: Incomplete
    PrivateNote: str
    DueDate: str
    ShipDate: str
    TrackingNum: str
    TotalAmt: str
    TxnDate: str
    ApplyTaxAfterDiscount: bool
    PrintStatus: str
    EmailStatus: str
    ExchangeRate: int
    GlobalTaxCalculation: str
    InvoiceLink: str
    HomeBalance: int
    HomeTotalAmt: int
    FreeFormAddress: bool
    EInvoiceStatus: Incomplete
    BillAddr: Incomplete
    ShipAddr: Incomplete
    BillEmail: Incomplete
    BillEmailCc: Incomplete
    BillEmailBcc: Incomplete
    CustomerRef: Incomplete
    CurrencyRef: Incomplete
    CustomerMemo: Incomplete
    DepartmentRef: Incomplete
    TxnTaxDetail: Incomplete
    DeliveryInfo: Incomplete
    RecurDataRef: Incomplete
    SalesTermRef: Incomplete
    ShipMethodRef: Incomplete
    TaxExemptionRef: Incomplete
    MetaData: Incomplete
    CustomField: Incomplete
    Line: Incomplete
    LinkedTxn: Incomplete
    def __init__(self) -> None: ...
    def to_linked_txn(self) -> LinkedTxn: ...
    @property
    def email_sent(self) -> bool: ...
    def to_ref(self) -> Ref: ...
