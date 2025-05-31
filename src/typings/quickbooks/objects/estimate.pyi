from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from ..mixins import QuickbooksPdfDownloadable as QuickbooksPdfDownloadable
from ..mixins import SendMixin as SendMixin
from .base import Address as Address
from .base import CustomerMemo as CustomerMemo
from .base import CustomField as CustomField
from .base import EmailAddress as EmailAddress
from .base import LinkedTxn as LinkedTxn
from .base import LinkedTxnMixin as LinkedTxnMixin
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

class Estimate(
    DeleteMixin,
    QuickbooksPdfDownloadable,
    QuickbooksManagedObject,
    QuickbooksTransactionEntity,
    LinkedTxnMixin,
    SendMixin,
):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    DocNumber: Incomplete
    TxnDate: Incomplete
    TxnStatus: Incomplete
    PrivateNote: Incomplete
    TotalAmt: int
    ExchangeRate: int
    ApplyTaxAfterDiscount: bool
    PrintStatus: str
    EmailStatus: str
    DueDate: Incomplete
    ShipDate: Incomplete
    ExpirationDate: Incomplete
    AcceptedBy: Incomplete
    AcceptedDate: Incomplete
    GlobalTaxCalculation: str
    BillAddr: Incomplete
    DepartmentRef: Incomplete
    ShipAddr: Incomplete
    ShipFromAddr: Incomplete
    BillEmail: Incomplete
    CustomerRef: Incomplete
    ProjectRef: Incomplete
    TxnTaxDetail: Incomplete
    CustomerMemo: Incomplete
    ClassRef: Incomplete
    SalesTermRef: Incomplete
    ShipMethodRef: Incomplete
    TrackingNum: str
    CustomField: Incomplete
    LinkedTxn: Incomplete
    Line: Incomplete
    def __init__(self) -> None: ...
