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
        # ("Online WLD Tips", ("32", 1)),
        ("Gift Card Tips", ("32", 1)),
        # ("Online WLD Gift Card Tips", ("32", 1)),
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


def create_daily_sales(txdate, daily_reports, overwrite=True):
    refresh_session()

    pattern = re.compile(r"\d+\.\d\d")

    store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}

    existing_receipts = {
        x.DepartmentRef.name if x.DepartmentRef else "20025": x
        for x in SalesReceipt.filter(TxnDate=qb_date_format(txdate), qb=CLIENT)
    }
    new_receipts = {}

    for store, sref in store_refs.items():
        if store in existing_receipts and store in daily_reports:
            if len(existing_receipts[store].LinkedTxn) > 0 and overwrite:
                logger.warning(
                    "overwriting existing linked transaction",
                    extra={
                        "store": store,
                        "receipt": json.loads(existing_receipts[store].to_json()),
                    },
                )
            elif len(existing_receipts[store].LinkedTxn) > 0 and not overwrite:
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
        elif store in daily_reports:
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
        logger.info(
            "Sales Overage Calculated",
            extra={"amount": str(line.Amount), "store": store, "txdate": str(txdate)},
        )
        line.SalesItemLineDetail = SalesItemLineDetail()
        item = Item.query("select * from Item where id = '{}'".format(31), qb=CLIENT)[0]
        line.SalesItemLineDetail.ItemRef = item.to_ref()
        line.SalesItemLineDetail.ServiceDate = None
        new_receipt.Line.append(line)
        daily_report["updatedAt"] = datetime.date.today().isoformat()

        new_receipt.PrivateNote = json.dumps(daily_report, indent=1)

        try:
            new_receipt.save(qb=CLIENT)
        except Exception as e:
            logger.exception(
                "Failed to save receipt",
                extra={"receipt": json.loads(new_receipt.to_json())},
            )

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
        minorversion=75,
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


def find_unmatched_deposits():
    refresh_session()
    where_clause = "TxnDate >= '2024-12-01' AND TxnDate < '2024-12-31'"
    qb_data_type = SalesReceipt
    query_count = qb_data_type.count(where_clause=where_clause, qb=CLIENT)
    r_count = 1
    logger.info(f"query_count: {query_count}")
    while r_count < query_count:
        sales_receipts = qb_data_type.where(
            where_clause=where_clause,
            order_by="TxnDate",
            start_position=r_count,
            max_results=1000,
            qb=CLIENT,
        )
        for sales_receipt in sales_receipts:
            if sales_receipt.TotalAmt > 0 and len(sales_receipt.LinkedTxn) == 0:
                logger.info(
                    "Found unmatched sales receipt",
                    extra={
                        "store": sales_receipt.DepartmentRef.name,
                        "TxnDate": sales_receipt.TxnDate,
                        "Amount": sales_receipt.TotalAmt,
                    },
                )
            r_count += 1


def fix_wld_online_tips():
    refresh_session()
    where_clause = "TxnDate >= '2024-01-04'"
    qb_data_type = SalesReceipt
    query_count = qb_data_type.count(where_clause=where_clause, qb=CLIENT)
    r_count = 1
    logger.info(f"query_count: {query_count}")
    while r_count < query_count:
        sales_receipts = qb_data_type.where(
            where_clause=where_clause,
            order_by="TxnDate",
            start_position=r_count,
            max_results=1000,
            qb=CLIENT,
        )
        for sales_receipt in sales_receipts:
            r_count += 1
            online_wld_tips = Decimal(0)
            online_wld_gift_card_tips = Decimal(0)
            online_wld_tips_line = None
            online_credit_card_line = None
            online_wld_gift_card_tips_line = None
            online_gift_card_line = None
            for line in sales_receipt.Line:
                if line.Description is None:
                    continue
                if line.Description.startswith("Online WLD Tips"):
                    online_wld_tips = line.Amount
                    if online_wld_tips == Decimal(0):
                        continue
                    online_wld_tips_line = line
                if line.Description.startswith("Online Credit Card"):
                    online_credit_card_line = line
                if line.Description.startswith("Online WLD Gift Card Tips"):
                    online_wld_gift_card_tips = line.Amount
                    online_wld_gift_card_tips_line = line
                if line.Description.startswith("Online Gift Card"):
                    online_gift_card_line = line
            for tip_line, total_line, tip_amount in [
                (online_wld_tips_line, online_credit_card_line, online_wld_tips),
                (
                    online_wld_gift_card_tips_line,
                    online_gift_card_line,
                    online_wld_gift_card_tips,
                ),
            ]:
                if tip_line is not None and total_line is not None:
                    sales_receipt.Line.remove(tip_line)
                    total_line.Amount = total_line.Amount + tip_amount
                    total_line.SalesItemLineDetail["Qty"] = 0
                    total_line.SalesItemLineDetail["UnitPrice"] = 0
                    try:
                        sales_receipt.save(qb=CLIENT)
                        logger.info(
                            "Fixed WLD online tips",
                            extra={
                                "sales_receipt": sales_receipt.DocNumber,
                                "store": sales_receipt.DepartmentRef.name,
                                "date": sales_receipt.TxnDate,
                            },
                        )
                    except Exception:
                        logger.exception(
                            "Failed to save sales receipt",
                            extra={
                                "sales_receipt": sales_receipt.DocNumber,
                                "store": sales_receipt.DepartmentRef.name,
                                "date": sales_receipt.TxnDate,
                                "online_wld_tips": online_wld_tips_line.to_json(),
                            },
                        )


def calculate_bill_splits(total_amount, line_amounts, locations, split_ratios=None):
    """Calculate how a bill should be split between locations.

    Args:
        total_amount (Decimal): Total bill amount
        line_amounts (list[Decimal]): List of line item amounts
        locations (list): List of location codes to split between
        split_ratios (dict, optional): Dictionary of {location: ratio} for custom splits.
                                     Defaults to equal splits.

    Returns:
        dict: Dictionary mapping locations to lists of line amounts

    Example:
        >>> amounts = calculate_bill_splits(
        ...     Decimal('256.36'),
        ...     [Decimal('256.36')],
        ...     ['20025', '20358', '20366', '20367', '20368']
        ... )
        >>> amounts['20025']
        [Decimal('51.27')]
        >>> sum(sum(v) for v in amounts.values())
        Decimal('256.36')
    """
    if not locations:
        raise ValueError("Must provide at least one location to split between")

    # Validate and normalize split ratios - keep full precision for calculations
    if split_ratios is None:
        split_ratios = {loc: Decimal("1") / len(locations) for loc in locations}
    else:
        # Convert any float ratios to Decimal but don't quantize yet
        split_ratios = {k: Decimal(str(v)) for k, v in split_ratios.items()}
        ratio_sum = sum(split_ratios.values())
        if abs(ratio_sum - Decimal("1")) > Decimal("0.001"):
            raise ValueError(f"Split ratios must sum to 1.0, got {ratio_sum}")

    # Initialize results dictionary
    results = {loc: [] for loc in locations}

    # Track running totals for each location
    location_totals = {loc: Decimal("0") for loc in locations}
    total_allocated = Decimal("0")

    # Process each line item
    for line_amount in line_amounts:
        remaining_amount = line_amount

        # Split the line amount between locations
        for location in locations[:-1]:  # Process all but last location
            ratio = split_ratios[location]
            exact_split = line_amount * ratio
            split_amount = exact_split.quantize(TWO_PLACES)

            results[location].append(split_amount)
            location_totals[location] += split_amount
            remaining_amount -= split_amount
            total_allocated += split_amount

        # Last location gets any remaining amount to ensure exact total
        last_location = locations[-1]
        results[last_location].append(remaining_amount.quantize(TWO_PLACES))
        location_totals[last_location] += remaining_amount
        total_allocated += remaining_amount

    # Verify totals
    if total_allocated != total_amount:
        raise ValueError(
            f"Split allocation mismatch: {total_allocated} != {total_amount}"
        )

    return results


def test_bill_split():
    """Test the bill splitting calculation with a specific test case."""
    # Test case: $256.36 split over 5 locations
    total = Decimal("256.36")
    line_amounts = [Decimal("256.36")]
    locations = ["20025", "20358", "20366", "20367", "20368"]

    try:
        splits = calculate_bill_splits(total, line_amounts, locations)

        # Print the results
        print("\nBill Split Test Results:")
        print(f"Original Amount: ${total}")
        print("\nSplit Amounts:")
        for loc, amounts in splits.items():
            loc_total = sum(amounts)
            print(f"{loc}: ${loc_total} {amounts}")

        # Verify total matches
        total_split = sum(sum(amounts) for amounts in splits.values())
        print(f"\nTotal Split Amount: ${total_split}")
        print(f"Matches Original: {total == total_split}")

        # Verify each location gets close to equal share
        expected_share = total / len(locations)
        print(f"\nExpected share per location: ${expected_share}")
        for loc, amounts in splits.items():
            loc_total = sum(amounts)
            diff = abs(loc_total - expected_share)
            print(f"{loc} diff from expected: ${diff}")

        return total == total_split

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        return False


def split_bill(original_bill, locations, split_ratios=None):
    """Split a QuickBooks bill between multiple locations."""
    refresh_session()

    # Calculate the splits first
    total_amount = sum(Decimal(line.Amount) for line in original_bill.Line)
    line_amounts = [Decimal(line.Amount) for line in original_bill.Line]

    try:
        split_amounts = calculate_bill_splits(
            total_amount, line_amounts, locations, split_ratios
        )
    except ValueError as e:
        logger.error("Failed to calculate bill splits", extra={"error": str(e)})
        raise

    store_refs = {x.Name: x.to_ref() for x in Department.all(qb=CLIENT)}

    # Verify all locations exist
    for location in locations:
        if location not in store_refs:
            raise ValueError(f"Invalid location code: {location}")

    # Create new bills first before voiding original
    new_bills = []
    split_doc_numbers = []
    i = 1

    try:
        for location in locations:
            new_bill = Bill()

            # Copy metadata from original
            new_bill.VendorRef = original_bill.VendorRef
            new_bill.TxnDate = original_bill.TxnDate
            new_bill.DueDate = getattr(original_bill, "DueDate", None)
            new_bill.SalesTermRef = getattr(original_bill, "SalesTermRef", None)
            new_bill.DepartmentRef = store_refs[location]

            # Generate split bill number
            new_bill.DocNumber = f"{original_bill.DocNumber}S{i}"
            split_doc_numbers.append(new_bill.DocNumber)

            new_bill.Line = []

            # Create line items using pre-calculated amounts
            for line_num, (orig_line, split_amount) in enumerate(
                zip(original_bill.Line, split_amounts[location]), 1
            ):
                new_line = AccountBasedExpenseLine()
                new_line.AccountBasedExpenseLineDetail = AccountBasedExpenseLineDetail()
                new_line.AccountBasedExpenseLineDetail.AccountRef = (
                    orig_line.AccountBasedExpenseLineDetail.AccountRef
                )
                new_line.LineNum = line_num
                new_line.Id = line_num
                new_line.Amount = split_amount
                new_line.Description = orig_line.Description
                new_bill.Line.append(new_line)

            # Add split documentation
            split_note = {
                "split_info": {
                    "original_doc_number": original_bill.DocNumber,
                    "split_date": datetime.datetime.now().isoformat(),
                    "total_splits": len(locations),
                    "split_locations": locations,
                    "split_amount": str(sum(split_amounts[location])),
                }
            }
            if hasattr(original_bill, "PrivateNote") and original_bill.PrivateNote:
                split_note["original_note"] = original_bill.PrivateNote
            new_bill.PrivateNote = json.dumps(split_note, indent=2)

            try:
                new_bill.save(qb=CLIENT)
                new_bills.append(new_bill)
                logger.info(
                    "Created split bill",
                    extra={
                        "original_doc": original_bill.DocNumber,
                        "split_doc": new_bill.DocNumber,
                        "location": location,
                        "amount": str(sum(split_amounts[location])),
                    },
                )
            except Exception as e:
                logger.exception(
                    "Failed to save split bill",
                    extra={"bill": new_bill.to_json(), "error": str(e)},
                )
                raise

            i += 1

        # Now void the original bill
        void_note = {
            "void_info": {
                "reason": "Split into multiple location bills",
                "void_date": datetime.datetime.now().isoformat(),
                "split_doc_numbers": split_doc_numbers,
            }
        }
        if hasattr(original_bill, "PrivateNote") and original_bill.PrivateNote:
            void_note["original_note"] = original_bill.PrivateNote

        original_bill.PrivateNote = json.dumps(void_note, indent=2)
        original_bill.save(qb=CLIENT)
        original_bill.delete(qb=CLIENT)

        logger.info(
            "Voided original bill after splitting",
            extra={
                "doc_number": original_bill.DocNumber,
                "split_docs": split_doc_numbers,
            },
        )

        return new_bills

    except Exception as e:
        logger.exception(
            "Bill split failed",
            extra={
                "original_doc": original_bill.DocNumber,
                "locations": locations,
                "error": str(e),
            },
        )
        # Attempt to void any created bills
        for bill in new_bills:
            try:
                bill.delete(qb=CLIENT)
            except:
                logger.exception(
                    "Failed to delete split bill during rollback",
                    extra={"doc_number": bill.DocNumber},
                )
        raise
