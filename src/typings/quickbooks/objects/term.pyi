from .base import QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

class Term(QuickbooksManagedObject, QuickbooksTransactionEntity):
    qbo_object_name: str
    Name: str
    Active: bool
    Type: Incomplete
    DiscountPercent: Incomplete
    DueDays: Incomplete
    DiscountDays: Incomplete
    DayOfMonthDue: Incomplete
    DueNextMonthDays: Incomplete
    DiscountDayOfMonth: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self): ...
