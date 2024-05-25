from ..mixins import FromJsonMixin as FromJsonMixin, ListMixin as ListMixin, ReadMixin as ReadMixin, ToDictMixin as ToDictMixin, ToJsonMixin as ToJsonMixin, UpdateMixin as UpdateMixin
from _typeshed import Incomplete

class QuickbooksBaseObject(ToJsonMixin, FromJsonMixin, ToDictMixin):
    class_dict: Incomplete
    list_dict: Incomplete
    detail_dict: Incomplete

class QuickbooksTransactionEntity(QuickbooksBaseObject):
    Id: Incomplete
    SyncToken: int
    sparse: bool
    domain: str
    def __init__(self) -> None: ...

class QuickbooksManagedObject(QuickbooksBaseObject, ReadMixin, ListMixin, UpdateMixin): ...
class QuickbooksReadOnlyObject(QuickbooksBaseObject, ReadMixin, ListMixin): ...

class MetaData(FromJsonMixin):
    CreateTime: str
    LastUpdatedTime: str
    def __init__(self) -> None: ...

class LinkedTxnMixin:
    def to_linked_txn(self): ...

class Address(QuickbooksBaseObject):
    Id: Incomplete
    Line1: str
    Line2: str
    Line3: str
    Line4: str
    Line5: str
    City: str
    CountrySubDivisionCode: str
    Country: str
    PostalCode: str
    Lat: str
    Long: str
    Note: str
    def __init__(self) -> None: ...

class PhoneNumber(ToJsonMixin, FromJsonMixin, ToDictMixin):
    FreeFormNumber: str
    def __init__(self) -> None: ...

class EmailAddress(QuickbooksBaseObject):
    Address: str
    def __init__(self) -> None: ...

class WebAddress(QuickbooksBaseObject):
    URI: str
    def __init__(self) -> None: ...

class Ref(QuickbooksBaseObject):
    value: str
    name: str
    type: str
    def __init__(self) -> None: ...

class CustomField(QuickbooksBaseObject):
    DefinitionId: str
    Type: str
    Name: str
    StringValue: str
    def __init__(self) -> None: ...

class LinkedTxn(QuickbooksBaseObject):
    qbo_object_name: str
    TxnId: int
    TxnType: int
    TxnLineId: int
    def __init__(self) -> None: ...

class CustomerMemo(QuickbooksBaseObject):
    value: str
    def __init__(self) -> None: ...

class MarkupInfo(QuickbooksBaseObject):
    class_dict: Incomplete
    PercentBased: bool
    Value: int
    Percent: int
    PriceLevelRef: Incomplete
    def __init__(self) -> None: ...

class AttachableRef(QuickbooksBaseObject):
    class_dict: Incomplete
    list_dict: Incomplete
    qbo_object_name: str
    LineInfo: Incomplete
    IncludeOnSend: bool
    Inactive: Incomplete
    NoRefOnly: Incomplete
    EntityRef: Incomplete
    CustomField: Incomplete
    def __init__(self) -> None: ...
