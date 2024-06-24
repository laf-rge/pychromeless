from .base import Address as Address, EmailAddress as EmailAddress, PhoneNumber as PhoneNumber, QuickbooksManagedObject as QuickbooksManagedObject, QuickbooksTransactionEntity as QuickbooksTransactionEntity, Ref as Ref, WebAddress as WebAddress
from _typeshed import Incomplete

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
    def to_ref(self): ...
