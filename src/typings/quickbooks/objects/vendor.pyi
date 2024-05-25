from .base import Address as Address, EmailAddress as EmailAddress, PhoneNumber as PhoneNumber, QuickbooksBaseObject as QuickbooksBaseObject, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref, WebAddress as WebAddress
from _typeshed import Incomplete

class ContactInfo(QuickbooksBaseObject):
    class_dict: Incomplete
    Type: str
    Telephone: Incomplete
    def __init__(self) -> None: ...

class Vendor(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Title: str
    GivenName: str
    MiddleName: str
    FamilyName: str
    Suffix: str
    CompanyName: str
    DisplayName: str
    PrintOnCheckName: str
    Active: bool
    TaxIdentifier: str
    Balance: int
    BillRate: int
    AcctNum: str
    Vendor1099: bool
    TaxReportingBasis: str
    BillAddr: Incomplete
    PrimaryPhone: Incomplete
    AlternatePhone: Incomplete
    Mobile: Incomplete
    Fax: Incomplete
    PrimaryEmailAddr: Incomplete
    WebAddr: Incomplete
    TermRef: Incomplete
    CurrencyRef: Incomplete
    APAccountRef: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self): ...
