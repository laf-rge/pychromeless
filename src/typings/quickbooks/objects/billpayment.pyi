from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from ..mixins import VoidMixin as VoidMixin
from .base import LinkedTxn as LinkedTxn
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class CheckPayment(QuickbooksBaseObject):
    class_dict: Incomplete
    qbo_object_name: str
    PrintStatus: str
    BankAccountRef: Incomplete
    def __init__(self) -> None: ...

class BillPaymentCreditCard(QuickbooksBaseObject):
    class_dict: Incomplete
    qbo_object_name: str
    CCAccountRef: Incomplete
    def __init__(self) -> None: ...

class BillPaymentLine(QuickbooksBaseObject):
    list_dict: Incomplete
    qbo_object_name: str
    Amount: int
    LinkedTxn: Incomplete
    def __init__(self) -> None: ...

class BillPayment(
    DeleteMixin,
    QuickbooksManagedObject,
    QuickbooksTransactionEntity,
    LinkedTxnMixin,
    VoidMixin,
):
    class_dict: Incomplete
    list_dict: Incomplete
    qbo_object_name: str
    PayType: str
    TotalAmt: int
    PrivateNote: str
    DocNumber: str
    VendorRef: Incomplete
    CheckPayment: Incomplete
    APAccountRef: Incomplete
    DepartmentRef: Incomplete
    CreditCardPayment: Incomplete
    CurrencyRef: Incomplete
    Line: Incomplete
    def __init__(self) -> None: ...
