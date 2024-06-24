from ..mixins import DeleteMixin as DeleteMixin, QuickbooksPdfDownloadable as QuickbooksPdfDownloadable, SendMixin as SendMixin
from .base import Address as Address, CustomField as CustomField, CustomerMemo as CustomerMemo, EmailAddress as EmailAddress, LinkedTxn as LinkedTxn, LinkedTxnMixin as LinkedTxnMixin, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from .detailline import DescriptionOnlyLine as DescriptionOnlyLine, DetailLine as DetailLine, DiscountLine as DiscountLine, GroupLine as GroupLine, SalesItemLine as SalesItemLine, SubtotalLine as SubtotalLine
from .tax import TxnTaxDetail as TxnTaxDetail
from _typeshed import Incomplete

class Estimate(DeleteMixin, QuickbooksPdfDownloadable, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin, SendMixin):
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
