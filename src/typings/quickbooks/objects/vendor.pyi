from _typeshed import Incomplete

from .base import Address as Address
from .base import EmailAddress as EmailAddress
from .base import PhoneNumber as PhoneNumber
from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .base import WebAddress as WebAddress

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
