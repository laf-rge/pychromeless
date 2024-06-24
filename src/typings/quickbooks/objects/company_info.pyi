from .base import Address as Address, EmailAddress as EmailAddress, MetaData as MetaData, PhoneNumber as PhoneNumber, QuickbooksManagedObject as QuickbooksManagedObject, Ref as Ref, WebAddress as WebAddress
from _typeshed import Incomplete

class CompanyInfo(QuickbooksManagedObject):
    class_dict: Incomplete
    qbo_object_name: str
    Id: Incomplete
    CompanyName: str
    LegalName: str
    CompanyStartDate: str
    FiscalYearStartMonth: str
    Country: str
    SupportedLanguages: str
    CompanyAddr: Incomplete
    CustomerCommunicationAddr: Incomplete
    LegalAddr: Incomplete
    PrimaryPhone: Incomplete
    Email: Incomplete
    WebAddr: Incomplete
    MetaData: Incomplete
    def __init__(self) -> None: ...
    def to_ref(self): ...
