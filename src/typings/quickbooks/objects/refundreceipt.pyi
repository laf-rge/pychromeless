from _typeshed import Incomplete
from quickbooks.objects import CreditCardPayment as CreditCardPayment

from ..mixins import DeleteMixin as DeleteMixin
from .base import Address as Address
from .base import CustomerMemo as CustomerMemo
from .base import CustomField as CustomField
from .base import EmailAddress as EmailAddress
from .base import LinkedTxn as LinkedTxn
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .detailline import DetailLine as DetailLine
from .tax import TxnTaxDetail as TxnTaxDetail

class RefundReceiptCheckPayment(QuickbooksBaseObject):
    qbo_object_name: str
    CheckNum: str
    Status: str
    NameOnAcct: str
    AcctNum: str
    BankName: str
    def __init__(self) -> None: ...

class RefundReceipt(
    DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin
):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    DocNumber: str
    TotalAmt: int
    ApplyTaxAfterDiscount: bool
    PrintStatus: str
    Balance: int
    PaymentRefNum: str
    TxnDate: str
    ExchangeRate: int
    PrivateNote: str
    PaymentType: str
    TxnSource: Incomplete
    GlobalTaxCalculation: str
    DepartmentRef: Incomplete
    CurrencyRef: Incomplete
    TxnTaxDetail: Incomplete
    DepositToAccountRef: Incomplete
    CustomerRef: Incomplete
    BillAddr: Incomplete
    ShipAddr: Incomplete
    ClassRef: Incomplete
    BillEmail: Incomplete
    PaymentMethodRef: Incomplete
    CheckPayment: Incomplete
    CreditCardPayment: Incomplete
    CustomerMemo: Incomplete
    CustomField: Incomplete
    Line: Incomplete
    LinkedTxn: Incomplete
    def __init__(self) -> None: ...
