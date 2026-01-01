from _typeshed import Incomplete

from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class Class(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Name: str
    SubClass: bool
    FullyQualifiedName: str
    Active: bool
    def __init__(self) -> None: ...
    def to_ref(self) -> Ref: ...
