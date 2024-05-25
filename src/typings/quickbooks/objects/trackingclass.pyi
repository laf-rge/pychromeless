from .base import QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

class Class(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Name: str
    SubClass: bool
    FullyQualifiedName: str
    Active: bool
    def __init__(self) -> None: ...
    def to_ref(self): ...
