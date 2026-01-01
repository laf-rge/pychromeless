from _typeshed import Incomplete

from .base import Address as Address
from .base import EmailAddress as EmailAddress
from .base import MetaData as MetaData
from .base import PhoneNumber as PhoneNumber
from .base import QuickbooksManagedObject as QuickbooksManagedObject
from .base import Ref as Ref
from .base import WebAddress as WebAddress

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
    def to_ref(self) -> Ref: ...
