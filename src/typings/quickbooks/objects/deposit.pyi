from decimal import Decimal
from ..mixins import DeleteMixin as DeleteMixin
from .base import AttachableRef as AttachableRef, CustomField as CustomField, LinkedTxn as LinkedTxn, LinkedTxnMixin as LinkedTxnMixin, QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete
from typing import Dict, Type, Any

class CashBackInfo(QuickbooksBaseObject):
    class_dict: Incomplete
    Amount: int
    Memo: str
    AccountRef: Incomplete
    def __init__(self) -> None: ...

class DepositLineDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    CheckNum: str
    TxnType: Incomplete
    Entity: Incomplete
    ClassRef: Incomplete
    AccountRef: Incomplete
    PaymentMethodRef: Incomplete
    def __init__(self) -> None: ...

class DepositLine(QuickbooksBaseObject):
    class_dict: Incomplete
    DepositLineDetail: DepositLineDetail
    DepositToAccountRef: Ref

    list_dict: Dict[str, Type[Any]] = {
        "LinkedTxn": LinkedTxn,
        "CustomField": CustomField,
    }

    qbo_object_name: str
    Id: Incomplete
    LineNum: int
    Description: str
    Amount: Decimal
    DetailType: str
    LinkedTxn: Incomplete
    CustomField: Incomplete
    def __init__(self) -> None: ...

class Deposit(DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete
    qbo_object_name: str
    TotalAmt: int
    HomeTotalAmt: int
    TxnDate: str
    DocNumber: str
    ExchangeRate: int
    GlobalTaxCalculation: str
    PrivateNote: str
    TxnStatus: str
    TxnSource: Incomplete
    DepositToAccountRef: Incomplete
    DepartmentRef: Incomplete
    CurrencyRef: Incomplete
    AttachableRef: Incomplete
    Line: Incomplete
    def __init__(self) -> None: ...
