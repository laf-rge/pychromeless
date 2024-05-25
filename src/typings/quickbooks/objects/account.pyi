from .base import QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

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
    def to_ref(self): ...
