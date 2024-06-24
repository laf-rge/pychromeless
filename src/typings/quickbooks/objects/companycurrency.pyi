from .base import CustomField as CustomField, MetaData as MetaData, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

class CompanyCurrency(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Id: Incomplete
    Code: str
    Name: str
    Active: bool
    CustomField: Incomplete
    MetaData: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self): ...
