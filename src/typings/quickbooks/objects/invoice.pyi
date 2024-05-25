from ..mixins import DeleteMixin as DeleteMixin, QuickbooksPdfDownloadable as QuickbooksPdfDownloadable, SendMixin as SendMixin, VoidMixin as VoidMixin
from .base import Address as Address, CustomField as CustomField, CustomerMemo as CustomerMemo, EmailAddress as EmailAddress, LinkedTxn as LinkedTxn, LinkedTxnMixin as LinkedTxnMixin, MetaData as MetaData, QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from .detailline import DescriptionOnlyLine as DescriptionOnlyLine, DetailLine as DetailLine, DiscountLine as DiscountLine, GroupLine as GroupLine, SalesItemLine as SalesItemLine, SubtotalLine as SubtotalLine
from .tax import TxnTaxDetail as TxnTaxDetail
from _typeshed import Incomplete

class DeliveryInfo(QuickbooksBaseObject):
    DeliveryType: str
    DeliveryTime: str
    def __init__(self) -> None: ...

class Invoice(DeleteMixin, QuickbooksPdfDownloadable, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin, SendMixin, VoidMixin):
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
    def to_linked_txn(self): ...
    @property
    def email_sent(self): ...
    def to_ref(self): ...
