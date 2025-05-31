from _typeshed import Incomplete
from quickbooks.mixins import PrefMixin as PrefMixin
from quickbooks.mixins import UpdateNoIdMixin as UpdateNoIdMixin

from .base import EmailAddress as EmailAddress
from .base import QuickbooksBaseObject as QuickbooksBaseObject
from .base import QuickbooksTransactionEntity as QuickbooksTransactionEntity
from .base import Ref as Ref

class PreferencesCustomField(QuickbooksBaseObject):
    Type: str
    Name: str
    StringValue: str
    BooleanValue: str
    def __init__(self) -> None: ...

class PreferencesCustomFieldGroup(QuickbooksBaseObject):
    list_dict: Incomplete
    def __init__(self) -> None: ...

class EmailMessageType(QuickbooksBaseObject):
    Message: str
    Subject: str
    def __init__(self) -> None: ...

class EmailMessagesPrefs(QuickbooksBaseObject):
    class_dict: Incomplete
    InvoiceMessage: Incomplete
    EstimateMessage: Incomplete
    SalesReceiptMessage: Incomplete
    StatementMessage: Incomplete
    def __init__(self) -> None: ...

class ProductAndServicesPrefs(QuickbooksBaseObject):
    QuantityWithPriceAndRate: bool
    ForPurchase: bool
    QuantityOnHand: bool
    ForSales: bool
    RevenueRecognition: bool
    RevenueRecognitionFrequency: str
    def __init__(self) -> None: ...

class ReportPrefs(QuickbooksBaseObject):
    ReportBasis: str
    CalcAgingReportFromTxnDate: bool
    def __init__(self) -> None: ...

class AccountingInfoPrefs(QuickbooksBaseObject):
    FirstMonthOfFiscalYear: str
    UseAccountNumbers: bool
    TaxYearMonth: str
    ClassTrackingPerTxn: bool
    TrackDepartments: bool
    TaxForm: str
    CustomerTerminology: str
    BookCloseDate: str
    DepartmentTerminology: str
    ClassTrackingPerTxnLine: bool
    def __init__(self) -> None: ...

class ClassTrackingPerTxnLine(QuickbooksBaseObject):
    ReportBasis: str
    CalcAgingReportFromTxnDate: bool
    def __init__(self) -> None: ...

class SalesFormsPrefs(QuickbooksBaseObject):
    class_dict: Incomplete
    detail_dict: Incomplete
    ETransactionPaymentEnabled: bool
    CustomTxnNumbers: bool
    AllowShipping: bool
    AllowServiceDate: bool
    ETransactionEnabledStatus: str
    DefaultCustomerMessage: str
    EmailCopyToCompany: bool
    AllowEstimates: bool
    DefaultTerms: Incomplete
    AllowDiscount: bool
    DefaultDiscountAccount: str
    DefaultShippingAccount: bool
    AllowDeposit: bool
    AutoApplyPayments: bool
    IPNSupportEnabled: bool
    AutoApplyCredit: bool
    CustomField: Incomplete
    UsingPriceLevels: bool
    ETransactionAttachPDF: bool
    UsingProgressInvoicing: bool
    EstimateMessage: str
    SalesEmailBcc: Incomplete
    SalesEmailCc: Incomplete
    def __init__(self) -> None: ...

class VendorAndPurchasesPrefs(QuickbooksBaseObject):
    class_dict: Incomplete
    detail_dict: Incomplete
    BillableExpenseTracking: bool
    TrackingByCustomer: bool
    TPAREnabled: bool
    POCustomField: Incomplete
    DefaultMarkupAccount: Incomplete
    DefaultTerms: Incomplete
    def __init__(self) -> None: ...

class TaxPrefs(QuickbooksBaseObject):
    class_dict: Incomplete
    TaxGroupCodeRef: Incomplete
    UsingSalesTax: bool
    PartnerTaxEnabled: bool
    def __init__(self) -> None: ...

class NameValue(QuickbooksBaseObject):
    Name: str
    Value: str
    def __init__(self) -> None: ...

class OtherPrefs(QuickbooksBaseObject):
    list_dict: Incomplete
    NameValue: Incomplete
    def __init__(self) -> None: ...

class TimeTrackingPrefs(QuickbooksBaseObject):
    WorkWeekStartDate: str
    MarkTimeEntriesBillable: bool
    ShowBillRateToAll: bool
    UseServices: bool
    BillCustomers: bool
    def __init__(self) -> None: ...

class CurrencyPrefs(QuickbooksBaseObject):
    class_dict: Incomplete
    HomeCurrency: Incomplete
    MultiCurrencyEnabled: bool
    def __init__(self) -> None: ...

class Preferences(PrefMixin, UpdateNoIdMixin, QuickbooksTransactionEntity):
    class_dict: Incomplete
    qbo_object_name: str
    EmailMessagesPrefs: Incomplete
    ProductAndServicesPrefs: Incomplete
    ReportPrefs: Incomplete
    AccountingInfoPrefs: Incomplete
    SalesFormsPrefs: Incomplete
    VendorAndPurchasesPrefs: Incomplete
    TaxPrefs: Incomplete
    OtherPrefs: Incomplete
    TimeTrackingPrefs: Incomplete
    CurrencyPrefs: Incomplete
    def __init__(self) -> None: ...
