from .base import Address as Address, EmailAddress as EmailAddress, MetaData as MetaData, PhoneNumber as PhoneNumber, QuickbooksReadOnlyObject as QuickbooksReadOnlyObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, WebAddress as WebAddress
from _typeshed import Incomplete

class CustomerType(QuickbooksReadOnlyObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Name: str
    Active: bool
    MetaData: Incomplete
    def __init__(self) -> None: ...
