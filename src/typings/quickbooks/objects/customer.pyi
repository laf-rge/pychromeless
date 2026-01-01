from _typeshed import Incomplete

from .base import Address as Address
from .base import EmailAddress as EmailAddress
from .base import PhoneNumber as PhoneNumber
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref
from .base import WebAddress as WebAddress

class Customer(QuickbooksManagedObject, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    Title: str
    GivenName: str
    MiddleName: str
    FamilyName: str
    Suffix: str
    FullyQualifiedName: str
    CompanyName: str
    DisplayName: str
    PrintOnCheckName: str
    Notes: str
    Active: bool
    IsProject: bool
    Job: bool
    BillWithParent: bool
    Taxable: bool
    Balance: int
    BalanceWithJobs: int
    PreferredDeliveryMethod: str
    ResaleNum: str
    Level: int
    OpenBalanceDate: str
    PrimaryTaxIdentifier: str
    BillAddr: Incomplete
    ShipAddr: Incomplete
    PrimaryPhone: Incomplete
    AlternatePhone: Incomplete
    Mobile: Incomplete
    Fax: Incomplete
    PrimaryEmailAddr: Incomplete
    WebAddr: Incomplete
    DefaultTaxCodeRef: Incomplete
    SalesTermRef: Incomplete
    PaymentMethodRef: Incomplete
    ParentRef: Incomplete
    ARAccountRef: Incomplete
    CurrencyRef: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self) -> Ref: ...
