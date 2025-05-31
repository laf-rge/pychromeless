from _typeshed import Incomplete

from .base import CustomField as CustomField
from .base import MetaData as MetaData
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

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
