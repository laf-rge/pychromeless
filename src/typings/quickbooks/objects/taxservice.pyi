from typing import Any

from _typeshed import Incomplete

from ..client import QuickBooks as QuickBooks
from ..mixins import UpdateMixin as UpdateMixin
from .base import QuickbooksBaseObject as QuickbooksBaseObject

class TaxRateDetails(QuickbooksBaseObject):
    qbo_object_name: str
    TaxRateName: Incomplete
    TaxRateId: Incomplete
    RateValue: Incomplete
    TaxAgencyId: Incomplete
    TaxApplicableOn: str
    def __init__(self) -> None: ...

class TaxService(QuickbooksBaseObject, UpdateMixin):
    list_dict: Incomplete
    qbo_object_name: str
    TaxCode: Incomplete
    TaxCodeId: Incomplete
    Id: int
    TaxRateDetails: Incomplete
    def __init__(self) -> None: ...
    def save(
        self,
        qb: Incomplete | None = None,
        request_id: Incomplete | None = None,
        params: Incomplete | None = None,
    ) -> Any: ...
