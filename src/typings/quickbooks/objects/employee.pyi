from .base import Address as Address, EmailAddress as EmailAddress, PhoneNumber as PhoneNumber, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref
from _typeshed import Incomplete

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
    def to_ref(self): ...
