from ..mixins import DeleteMixin as DeleteMixin
from .base import Address as Address, CustomField as CustomField, CustomerMemo as CustomerMemo, EmailAddress as EmailAddress, LinkedTxnMixin as LinkedTxnMixin, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from .tax import TxnTaxDetail as TxnTaxDetail
from _typeshed import Incomplete
from quickbooks.objects.detailline import DescriptionOnlyLine as DescriptionOnlyLine, DetailLine as DetailLine, DiscountLine as DiscountLine, SalesItemLine as SalesItemLine, SubtotalLine as SubtotalLine

class CreditMemo(DeleteMixin, QuickbooksTransactionEntity, QuickbooksManagedObject, LinkedTxnMixin):
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
    def to_ref(self): ...
