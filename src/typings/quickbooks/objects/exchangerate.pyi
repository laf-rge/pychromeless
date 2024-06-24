from .base import CustomField as CustomField, QuickbooksBaseObject as QuickbooksBaseObject
from _typeshed import Incomplete
from quickbooks.mixins import FromJsonMixin as FromJsonMixin, ListMixin as ListMixin, UpdateNoIdMixin as UpdateNoIdMixin

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
