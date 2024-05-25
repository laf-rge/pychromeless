from ..mixins import DeleteMixin as DeleteMixin, VoidMixin as VoidMixin
from .base import LinkedTxn as LinkedTxn, LinkedTxnMixin as LinkedTxnMixin, QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

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

class BillPayment(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin, VoidMixin):
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
