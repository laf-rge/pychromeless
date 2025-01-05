import base64
import calendar
import datetime
import json
import re
import logging
from collections import OrderedDict
from decimal import Decimal
from functools import reduce
from locale import LC_NUMERIC, atof, setlocale

from boto3.session import Session
from botocore.exceptions import ClientError
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.helpers import qb_date_format
from quickbooks.objects import (
    Account,
    AccountBasedExpenseLine,
    AccountBasedExpenseLineDetail,
    Bill,
    Customer,
    Department,
    Deposit,
    DepositLine,
    DepositLineDetail,
    Item,
    JournalEntry,
    JournalEntryLine,
    JournalEntryLineDetail,
    SalesItemLine,
    SalesItemLineDetail,
    SalesReceipt,
    Vendor,
    VendorCredit,
)

logger = logging.getLogger(__name__)

# warning! this won't work if we multiply
TWO_PLACES = Decimal(10) ** -2
setlocale(LC_NUMERIC, "")
AUTH_CLIENT = None
CLIENT = None

detail_map = OrderedDict(
    [
        ("Pre-Discount Sales", ("1", 1)),  # Sales
        ("Discounts", ("35", -1)),  # Discounts
        # ("Register Audit (CID)", ("33", -1)), #Pay Out
        ("House Account", ("24", -1)),
        ("Online Gift Card", ("38", -1)),
        ("Gift Card", ("30", -1)),
        ("Online Credit Card", ("37", -1)),
        ("InStore Credit Card", ("28", -1)),
        ("DoorDash", ("46", -1)),
        ("GrubHub", ("48", -1)),
        ("UberEats", ("47", -1)),
        ("EZ Cater", ("49", -1)),
        ("Remote Payment", ("45", -1)),
        ("Gift Cards Sold", ("34", 1)),
        ("Sales Tax", ("15", 1)),
        ("Donations", ("36", 1)),
        ("Online CC Tips", ("32", 1)),
        ("Online WLD Tips", ("32", 1)),
        ("CC Tips", ("32", 1)),
    ]
)

gl_code_map = {
    "1700": "1980",  # security deposit
    "2400": "6280",  # Sales Tax Payable
    "4000": "1201",  # Sales (stouborn soda?)
    "5010": "1201",  # Food Other
    "5010.1": "1201",  # Bread
    "5010.2": "1201",  # Chips
    "5010.3": "1201",  # Cookies
    "5010.5": "1201",  # Meat
    "5010.6": "1201",  # Cheese
    "5010.8": "1201",  # Retail - (CPR Jar)
    "5020": "1201",  # Paper
    "5030": "1201",  # Beverages Other
    "5030.1": "1201",  # Beverages Fountain
    "5030.2": "1201",  # Beverages Bottles
    "5040": "1201",  # Produce
    "6243": "6056",  # Kitchen
    "6244": "6057",  # Kitchen - Gloves
    "6245": "6056",  # Kitchen - Cleaning Supplies
    "6253": "1201",  # Ops: Comps -> inventory uncat
    "6293": "5301",  # Min Order Charge -> COGS - Delivery
    "6291": "5301",  # Fule Surcharge -> COGS - Delivery
    "6340": "5301",  # Ops: Miscellaneous
    "8026": "6280",
    "6290": "1201",  # Ops
}  # Sales and Use Tax

gl_code_map_to_cogs = {
    "1700": "1995",  # security deposit
    "2400": "6280",  # Sales Tax Payable
    "4000": "5102",  # Sales (stouborn soda?)
    "5010": "5103",  # Food Other
    "5010.1": "5104",  # Bread
    "5010.2": "5105",  # Chips
    "5010.3": "5106",  # Cookies
    "5010.4": "5110",  # Soup
    "5010.5": "5107",  # Meat
    "5010.6": "5108",  # Cheese
    "5010.8": "5103",  # CPR Jar
    "5020": "5201",  # Paper
    "5030": "5100",  # Beverages Other
    "5030.1": "5101",  # Beverages Fountain
    "5030.2": "5102",  # Beverages Bottles
    "5040": "5109",  # Produce
    "6243": "6056",  # Kitchen
    "6244": "6057",  # Kitchen - Gloves
    "6245": "6056",  # Kitchen - Cleaning Supplies
    "6293": "5301",  # Min Order Charge -> COGS - Delivery
    "6340": "5301",  # Ops: Miscellaneous
    "8026": "6280",  # Sales and Use Tax
}

third_party_map = {
    "DoorDash": "1361",
    "UberEats": "1362",
    "GrubHub": "1363",
    "EZ Cater": "1364",
    "Total": "1360",
}

account_ref = None

inv_account_ref = None

vendor = None


def lambda_handler(event, context):
    refresh_session()
    return {"statusCode": 200, "body": get_secret()}


def update_royalty(year, month, payment_data):
    refresh_session()

    supplier = Vendor.where("DisplayName like 'A Sub Above'", qb=CLIENT)[0]

    for store, payment_info in payment_data.items():
        lines = [
            [wmc_account_ref(6041), "", payment_info["Royalty"]],
            [wmc_account_ref(6042), "", payment_info["Advertising"]],
            [wmc_account_ref(6044), "", payment_info["Media"]],
            [wmc_account_ref(6043), "", payment_info["CoOp"]],
            [
                wmc_account_ref(2370),
                "",
                "-"
                + str(
                    (
                        Decimal(payment_info["Royalty"].replace(",", ""))
                        + Decimal(payment_info["Advertising"].replace(",", ""))
                        + Decimal(payment_info["Media"].replace(",", ""))
                        + Decimal(payment_info["CoOp"].replace(",", ""))
                    ).quantize(TWO_PLACES)
                ),
            ],
        ]

        sync_bill(
            supplier,
            "royalty" + store + str(year * 100 + month),
            datetime.date(year, month, calendar.monthrange(year, month)[1]),
            json.dumps(payment_info),
            lines,
            store,
        )
    return


def create_daily_sales(txdate, daily_reports):
    refresh_session()

    pattern = re.compile(r"\d+\.\d\d")

    store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}

    existing_receipts = {
        x.DepartmentRef.name if x.DepartmentRef else "20025": x
        for x in SalesReceipt.filter(TxnDate=qb_date_format(txdate), qb=CLIENT)
    }
    new_receipts = {}

    for store, sref in store_refs.items():
        if store in existing_receipts:
            if len(existing_receipts[store].LinkedTxn) > 0:
                logger.warning(
                    "skipping already linked transaction",
                    extra={
                        "store": store,
                        "receipt": existing_receipts[store].to_json(),
                    },
                )
                continue
            new_receipts[store] = existing_receipts[store]
            # clear old lines
            new_receipts[store].Line.clear()
        else:
            new_receipts[store] = SalesReceipt()

    for store, new_receipt in new_receipts.items():
        if store not in daily_reports:
            continue
        new_receipts[store].DepartmentRef = store_refs[store]
        new_receipt.TxnDate = qb_date_format(txdate)
        new_receipt.CustomerRef = Customer.all(qb=CLIENT)[0].to_ref()
        daily_report = daily_reports[store]

        line_num = 1
        amount_total = Decimal(0.0)
        for line_item, line_id in detail_map.items():
            line = SalesItemLine()
            line.LineNum = line_num
            if line_item in daily_report and daily_report[line_item]:
                if daily_report[line_item].startswith("N"):
                    line.Amount = Decimal(0)
                else:
                    line.Amount = (
                        Decimal(atof(daily_report[line_item].strip("$"))) * line_id[1]
                    )
                amount_total += Decimal(line.Amount)
                line.Description = "{} imported from ({})".format(
                    line_item, daily_report[line_item]
                )
            else:
                line.Amount = Decimal(0)
                line.Description = "Nothing captured."
            line.SalesItemLineDetail = SalesItemLineDetail()
            item = Item.query(
                "select * from Item where id = '{}'".format(line_id[0]), qb=CLIENT
            )[0]
            line.SalesItemLineDetail.ItemRef = item.to_ref()
            line.SalesItemLineDetail.ServiceDate = None
            new_receipt.Line.append(line)
            line_num += 1

        # Payin
        line = SalesItemLine()
        line.LineNum = line_num
        line_num += 1
        line.Description = daily_report["Payins"].strip()
        if line.Description.count("\n") > 0:
            amount = Decimal(0)
            for payin_line in line.Description.split("\n")[1:]:
                if payin_line.startswith("TOTAL"):
                    continue
                mg = pattern.search(payin_line)
                if mg:
                    amount = amount + Decimal(atof(mg.group()))
            line.Amount = amount.quantize(TWO_PLACES)
            amount_total += amount
        else:
            line.Amount = Decimal(0)
        line.SalesItemLineDetail = SalesItemLineDetail()
        item = Item.query("select * from Item where id = '{}'".format(43), qb=CLIENT)[0]
        line.SalesItemLineDetail.ItemRef = item.to_ref()
        line.SalesItemLineDetail.ServiceDate = None
        new_receipt.Line.append(line)

        # Register Audit
        line = SalesItemLine()
        line.LineNum = line_num
        line_num += 1
        line.Description = daily_report["Bank Deposits"].strip()
        # test if there was a recorded deposit
        if line.Description:
            line.Amount = Decimal(atof(line.Description.split()[4])) - Decimal(
                amount_total
            ).quantize(TWO_PLACES)
        else:
            line.Amount = Decimal(0)
        line.SalesItemLineDetail = SalesItemLineDetail()
        item = Item.query("select * from Item where id = '{}'".format(31), qb=CLIENT)[0]
        line.SalesItemLineDetail.ItemRef = item.to_ref()
        line.SalesItemLineDetail.ServiceDate = None
        new_receipt.Line.append(line)

        new_receipt.PrivateNote = json.dumps(daily_report, indent=1)

        new_receipt.save(qb=CLIENT)

    return


def enter_online_cc_fee(year, month, payment_data):
    refresh_session()

    supplier = Vendor.where("DisplayName like 'Jersey Mike%'", qb=CLIENT)[0]
    for store, payment_info in payment_data.items():
        lines = [[wmc_account_ref(6210), "", payment_data[store]["Total Fees"]]]

        sync_bill(
            supplier,
            "cc" + store + str(year * 100 + month),
            datetime.date(year, month, calendar.monthrange(year, month)[1]),
            json.dumps(payment_data[store]),
            lines,
            store,
        )
    return


def sync_third_party_deposit(supplier, deposit_date, notes, lines, department=None):
    refresh_session()

    store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}

    # check if one already exists
    query = Deposit.filter(TxnDate=qb_date_format(deposit_date), qb=CLIENT)
    for d in query:
        if (
            d.DepartmentRef is None
            if not department
            else store_refs[department]
            and Decimal(d.Line[0].Amount).quantize(TWO_PLACES)
            == Decimal(atof(lines[0][2])).quantize(TWO_PLACES)
        ):
            logger.warning(
                "Skipping already imported deposit",
                extra={
                    "date": qb_date_format(deposit_date),
                    "store": department,
                    "amount": lines[0][2],
                },
            )
            return
    deposit = Deposit()
    deposit.TxnDate = qb_date_format(deposit_date)
    deposit.PrivateNote = notes
    deposit.DepartmentRef = None if not department else store_refs[department]
    deposit.DepositToAccountRef = wmc_account_ref(1010)

    line_num = 1

    for deposit_line in lines:
        line = DepositLine()
        line.DepositLineDetail = DepositLineDetail()
        line.DepositLineDetail.AccountRef = wmc_account_ref(int(deposit_line[0]))
        line.DepositLineDetail.Entity = Vendor.filter(DisplayName=supplier, qb=CLIENT)[
            0
        ].to_ref()
        line.LineNum = line_num
        line.Id = line_num
        line.Amount = Decimal(atof(deposit_line[2])).quantize(TWO_PLACES)
        line.Description = deposit_line[1]
        line_num += 1
        deposit.Line.append(line)

    try:
        deposit.save(qb=CLIENT)
    except Exception:
        logger.exception("Failed to save deposit", extra={"deposit": deposit.to_json()})


def sync_bill(supplier, invoice_num, invoice_date, notes, lines, department=None):
    refresh_session()

    store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}

    # is this a credit
    if reduce(lambda x, y: x + atof(y[-1]), lines, 0.0) < -0.08:
        tx_type = VendorCredit
        item_sign = -1
    else:
        item_sign = 1
        tx_type = Bill

    # see if the invoice number already exists
    query = tx_type.filter(DocNumber=invoice_num, qb=CLIENT)
    if len(query) == 0:
        # create the bill
        bill = tx_type()
        bill.DocNumber = invoice_num
    else:
        bill = query[0]

    if len(getattr(bill, "LinkedTxn", [])) > 0:
        logger.warning("Skipping linked invoice", extra={"invoice_num": invoice_num})
        return

    bill.TxnDate = qb_date_format(invoice_date)

    bill.VendorRef = supplier.to_ref()

    bill.PrivateNote = notes
    bill.DepartmentRef = None if not department else store_refs[department]

    if isinstance(bill, Bill):
        bill.SalesTermRef = supplier.TermRef
        bill.DueDate = None

    # clear the lines
    bill.Line = []

    line_num = 1

    for bill_line in lines:
        line = AccountBasedExpenseLine()
        line.AccountBasedExpenseLineDetail = AccountBasedExpenseLineDetail()
        line.AccountBasedExpenseLineDetail.AccountRef = bill_line[0]
        line.LineNum = line_num
        line.Id = line_num
        line.Amount = Decimal(atof(bill_line[2])).quantize(TWO_PLACES) * item_sign
        line.Description = bill_line[1]
        line_num += 1
        bill.Line.append(line)

    try:
        bill.save(qb=CLIENT)
    except Exception:
        logger.exception("Failed to save bill", extra={"bill": bill.to_json()})


def sync_third_party_transactions(year, month, payment_data):
    refresh_session()

    store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}

    for store, store_data in payment_data.items():
        entries = JournalEntry.where(
            "DocNumber = 'tp-{0}-{2}-{1}'".format(store, str(month).zfill(2), year),
            qb=CLIENT,
        )
        if len(entries) == 0:
            # create the JournalEntry
            jentry = JournalEntry()
            jentry.DocNumber = "tp-{0}-{2}-{1}".format(store, str(month).zfill(2), year)
        else:
            jentry = entries[0]

        jentry.TxnDate = qb_date_format(
            datetime.date(year, month, calendar.monthrange(year, month)[1])
        )
        jentry.PrivateNote = str(payment_data)

        # clear the lines
        jentry.Line = []

        line_num = 1

        for payment_name, amount in store_data.items():
            line = JournalEntryLine()
            line.JournalEntryLineDetail = JournalEntryLineDetail()
            line.JournalEntryLineDetail.AccountRef = wmc_account_ref(
                third_party_map[payment_name]
            )
            line.JournalEntryLineDetail.DepartmentRef = (
                None if not store else store_refs[store]
            )
            line.JournalEntryLineDetail.PostingType = "Debit"
            line.LineNum = line_num
            line.Id = line_num
            line.Amount = Decimal(atof(amount)).quantize(TWO_PLACES)
            if payment_name == "Total":
                line.JournalEntryLineDetail.PostingType = "Credit"
            line.Description = payment_name
            line_num += 1
            jentry.Line.append(line)

        try:
            jentry.save(qb=CLIENT)
        except Exception:
            logger.exception(
                "Failed to save journal entry",
                extra={"journal_entry": jentry.to_json()},
            )


def sync_inventory(year, month, lines, notes, total, department):
    refresh_session()

    store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}

    entries = JournalEntry.where(
        "DocNumber = 'inv-{0}-{2}-{1}'".format(department, str(month).zfill(2), year),
        qb=CLIENT,
    )
    if len(entries) == 0:
        # create the JournalEntry
        jentry = JournalEntry()
        jentry.DocNumber = "inv-{0}-{2}-{1}".format(
            department, str(month).zfill(2), year
        )
    else:
        jentry = entries[0]
    jentry.TxnDate = qb_date_format(
        datetime.date(year, month, calendar.monthrange(year, month)[1])
    )
    jentry.PrivateNote = notes

    # clear the lines
    jentry.Line = []

    line_num = 1

    for jentry_line in lines:
        line = JournalEntryLine()
        line.JournalEntryLineDetail = JournalEntryLineDetail()
        line.JournalEntryLineDetail.AccountRef = jentry_line[0]
        line.JournalEntryLineDetail.DepartmentRef = (
            None if not department else store_refs[department]
        )
        line.JournalEntryLineDetail.PostingType = "Debit"
        line.LineNum = line_num
        line.Id = line_num
        line.Amount = Decimal(atof(jentry_line[1])).quantize(TWO_PLACES)
        if line.Amount < 0:
            line.JournalEntryLineDetail.PostingType = "Credit"
            line.Amount = line.Amount * -1
        line.Description = jentry_line[2]
        line_num += 1
        jentry.Line.append(line)

    line = JournalEntryLine()
    line.JournalEntryLineDetail = JournalEntryLineDetail()
    line.JournalEntryLineDetail.AccountRef = wmc_account_ref("1201")
    line.JournalEntryLineDetail.DepartmentRef = (
        None if not department else store_refs[department]
    )
    line.JournalEntryLineDetail.PostingType = "Credit"
    line.LineNum = line_num
    line.Id = line_num
    line.Amount = Decimal(atof(total)).quantize(TWO_PLACES)
    line_num += 1
    jentry.Line.append(line)

    try:
        jentry.save(qb=CLIENT)
    except Exception:
        logger.exception(
            "Failed to save journal entry",
            extra={"journal_entry": jentry.to_json()},
        )


def wmc_account_ref(acctNum):
    global account_ref
    if account_ref is None:
        refresh_session()
        account_ref = dict(
            map(
                lambda x: (x.AcctNum, x.to_ref()),
                Account.all(max_results=1000, qb=CLIENT),
            )
        )
    return account_ref[str(acctNum)]


def account_ref_lookup(gl_account_code):
    global account_ref
    if account_ref is None:
        refresh_session()
        account_ref = dict(
            map(
                lambda x: (x.AcctNum, x.to_ref()),
                Account.all(max_results=1000, qb=CLIENT),
            )
        )

    return account_ref[gl_code_map[gl_account_code]]


def inventory_ref_lookup(inv_account_code):
    global inv_account_ref
    if inv_account_ref is None:
        refresh_session()
        inv_account_ref = dict(
            map(
                lambda x: (x.AcctNum, x.to_ref()),
                Account.all(max_results=1000, qb=CLIENT),
            )
        )

    return inv_account_ref[gl_code_map_to_cogs[inv_account_code]]


def vendor_lookup(gl_vendor_name):
    global vendor
    if vendor is None:
        refresh_session()
        vendor = {
            "WNEPLS": Vendor.where("DisplayName like 'The Paper%'", qb=CLIENT)[0],
            "PR-D&D": Vendor.where("DisplayName like 'D&D%'", qb=CLIENT)[0],
            "PEPSI": Vendor.where("DisplayName like 'Pepsi%'", qb=CLIENT)[0],
            "GenPro": Vendor.where("DisplayName like 'General Produce'", qb=CLIENT)[0],
            "SYSFRA": Vendor.where("DisplayName like 'Sysco San%'", qb=CLIENT)[0],
            "SYSSAC": Vendor.where("DisplayName like 'Sysco Sac%'", qb=CLIENT)[0],
            "SAL": Vendor.where("DisplayName like 'Sala%'", qb=CLIENT)[0],
            "DONOGH": Vendor.where("DisplayName like 'Donoghue%'", qb=CLIENT)[0],
        }
    return vendor[gl_vendor_name]


def refresh_session():
    global AUTH_CLIENT
    global CLIENT
    s = json.loads(get_secret())

    if AUTH_CLIENT is None:
        AUTH_CLIENT = AuthClient(
            client_id=s["client_id"],
            client_secret=s["client_secret"],
            redirect_uri=s["redirect_url"],
            access_token=s["access_token"],
            refresh_token=s["refresh_token"],
            environment="production",
        )
    # if we already created one and the secret has updated lets use the new one
    AUTH_CLIENT.access_token = s["access_token"]
    AUTH_CLIENT.refresh_token = s["refresh_token"]
    # caution! invalid requests return {"error":"invalid_grant"} quietly
    AUTH_CLIENT.refresh()
    s["access_token"] = AUTH_CLIENT.access_token
    s["refresh_token"] = AUTH_CLIENT.refresh_token
    put_secret(json.dumps(s))
    # QuickBooks.enable_global()
    CLIENT = QuickBooks(
        auth_client=AUTH_CLIENT,
        company_id="1401432085",
        minorversion=70,
        use_decimal=True,
    )
    return CLIENT


secret_name = "prod/qbo"
region_name = "us-east-2"

# Create a Secrets Manager client
session = Session()
client = session.client(service_name="secretsmanager", region_name=region_name)


def get_secret() -> bytes | str:
    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.
    get_secret_value_response = None
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "DecryptionFailureException":
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif error_code == "InternalServiceErrorException":
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif error_code == "InvalidParameterException":
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif error_code == "InvalidRequestException":
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif error_code == "ResourceNotFoundException":
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        else:
            # Handle any other unexpected errors
            raise e
    # Decrypts secret using the associated KMS CMK.
    # Depending on whether the secret is a string or binary, one of these fields will be populated.
    if get_secret_value_response:
        if "SecretString" in get_secret_value_response:
            return get_secret_value_response["SecretString"]
        else:
            return base64.b64decode(get_secret_value_response["SecretBinary"])
    else:
        raise Exception("Secrets issue.")


def put_secret(secret_string):
    put_secret_value_response = client.put_secret_value(
        SecretId=secret_name, SecretString=secret_string
    )
    return put_secret_value_response


def bill_export():
    refresh_session()
    # store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}
    for qb_data_type in [VendorCredit, Bill, SalesReceipt, Deposit, JournalEntry]:
        with open(
            "purchase_{0}_journal.json".format(qb_data_type.__name__), "w"
        ) as fileout:
            fileout.write("[")
            query_count = qb_data_type.count(
                where_clause="TxnDate > '2020-06-01' AND TxnDate < '2023-06-07'",
                qb=CLIENT,
            )
            r_count = 1
            while r_count < query_count:
                bills = qb_data_type.where(
                    where_clause="TxnDate >= '2020-06-01' AND TxnDate < '2023-06-07'",
                    order_by="TxnDate",
                    start_position=r_count,
                    max_results=1000,
                    qb=CLIENT,
                )
                for bill in bills:
                    if (
                        not hasattr(bill, "DepartmentRef")
                        or bill.DepartmentRef is None
                        or bill.DepartmentRef.name in (None, "WMC", "20025")
                    ):
                        fileout.write(bill.to_json())
                        fileout.write(",\n")
                    r_count += 1
            fileout.write("]")


def fix_deposit():
    refresh_session()
    store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}
    qb_data_type = Deposit
    modify_queue = []
    with open(
        "purchase_{0}_journal.json".format(qb_data_type.__name__), "w"
    ) as fileout:
        fileout.write("[")
        query_count = qb_data_type.count(
            where_clause="TxnDate >= '2022-01-01' AND TxnDate < '2023-01-01'", qb=CLIENT
        )
        r_count = 1
        while r_count < query_count:
            bills = qb_data_type.where(
                where_clause="TxnDate >= '2022-01-01' AND TxnDate < '2023-01-01'",
                order_by="TxnDate",
                start_position=r_count,
                max_results=1000,
                qb=CLIENT,
            )
            for bill in bills:
                if (
                    not hasattr(bill, "DepartmentRef")
                    or bill.DepartmentRef is None
                    or bill.DepartmentRef.name == "20025"
                ):
                    if (
                        hasattr(bill.Line[0], "DepositLineDetail")
                        and bill.Line[0].DepositLineDetail.AccountRef.name
                        == "1330 Other Current Assets:Gift Cards"
                    ):
                        if "20358" in bill.Line[0].Description:
                            logger.info(
                                "Found deposit",
                                extra={
                                    "bill": bill.to_json(),
                                    "bill.Line[0].Description": bill.Line[
                                        0
                                    ].Description,
                                },
                            )
                            modify_queue.append(bill)
                r_count += 1
        for bill in modify_queue:
            bill.DepartmentRef = store_refs["20358"]
            # bill.save(qb=CLIENT)
