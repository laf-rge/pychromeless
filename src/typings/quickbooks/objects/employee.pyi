from _typeshed import Incomplete

from .base import Address as Address
from .base import EmailAddress as EmailAddress
from .base import PhoneNumber as PhoneNumber
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class Employee(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    SSN: str
    GivenName: str
    FamilyName: str
    MiddleName: str
    DisplayName: str
    Suffix: str
    PrintOnCheckName: str
    EmployeeNumber: str
    Title: str
    BillRate: int
    CostRate: int
    BirthDate: str
    Gender: Incomplete
    HiredDate: str
    ReleasedDate: str
    Active: bool
    Organization: bool
    BillableTime: bool
    PrimaryAddr: Incomplete
    PrimaryPhone: Incomplete
    Mobile: Incomplete
    EmailAddress: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self) -> Ref: ...
