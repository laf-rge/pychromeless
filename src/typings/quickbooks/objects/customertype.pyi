from _typeshed import Incomplete

from .base import Address as Address
from .base import EmailAddress as EmailAddress
from .base import MetaData as MetaData
from .base import PhoneNumber as PhoneNumber
from .base import QuickbooksReadOnlyObject as QuickbooksReadOnlyObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import WebAddress as WebAddress

class CustomerType(QuickbooksReadOnlyObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Name: str
    Active: bool
    MetaData: Incomplete
    def __init__(self) -> None: ...
