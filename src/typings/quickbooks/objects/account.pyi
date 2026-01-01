from _typeshed import Incomplete

from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class Account(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Name: str
    SubAccount: bool
    FullyQualifiedName: str
    Active: bool
    Classification: Incomplete
    AccountType: Incomplete
    AccountSubType: str
    Description: str
    AcctNum: str
    CurrentBalance: Incomplete
    CurrentBalanceWithSubAccounts: Incomplete
    CurrencyRef: Incomplete
    ParentRef: Incomplete
    TaxCodeRef: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self) -> Ref: ...
