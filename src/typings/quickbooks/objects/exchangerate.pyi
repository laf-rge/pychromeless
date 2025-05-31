from _typeshed import Incomplete
from quickbooks.mixins import FromJsonMixin as FromJsonMixin
from quickbooks.mixins import ListMixin as ListMixin
from quickbooks.mixins import UpdateNoIdMixin as UpdateNoIdMixin

from .base import CustomField as CustomField
from .base import QuickbooksBaseObject as QuickbooksBaseObject

class ExchangeRateMetaData(FromJsonMixin):
    LastUpdatedTime: str
    def __init__(self) -> None: ...

class ExchangeRate(QuickbooksBaseObject, ListMixin, UpdateNoIdMixin):
    class_dict: Incomplete
    qbo_object_name: str
    AsOfDate: str
    SourceCurrencyCode: str
    Rate: int
    TargetCurrencyCode: str
    MetaData: Incomplete
    CustomField: Incomplete
    def __init__(self) -> None: ...
