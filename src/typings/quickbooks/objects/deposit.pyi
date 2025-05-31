from decimal import Decimal
from typing import Any, Dict, Type

from _typeshed import Incomplete

from ..mixins import DeleteMixin as DeleteMixin
from .base import AttachableRef as AttachableRef
from .base import CustomField as CustomField
from .base import LinkedTxn as LinkedTxn
from .base import LinkedTxnMixin as LinkedTxnMixin
from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

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

class Deposit(
    DeleteMixin, QuickbooksManagedObject, QuickbooksTransactionEntity, LinkedTxnMixin
):
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
