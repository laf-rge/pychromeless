from _typeshed import Incomplete

from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

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
