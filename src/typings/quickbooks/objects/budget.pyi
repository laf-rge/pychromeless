from .base import QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksReadOnlyObject as QuickbooksReadOnlyObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

class BudgetDetail(QuickbooksBaseObject):
    class_dict: Incomplete
    BudgetDate: str
    Amount: int
    AccountRef: Incomplete
    CustomerRef: Incomplete
    ClassRef: Incomplete
    DepartmentRef: Incomplete
    def __init__(self) -> None: ...

class Budget(QuickbooksReadOnlyObject, QuickbooksTransactionEntity):
    list_dict: Incomplete
    qbo_object_name: str
    Name: str
    StartDate: str
    EndDate: str
    BudgetType: str
    BudgetEntryType: str
    Active: bool
    BudgetDetail: Incomplete
    def __init__(self) -> None: ...
