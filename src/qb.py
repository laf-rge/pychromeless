import json
import boto3
import base64
import re
import calendar
import datetime
from functools import reduce
from botocore.exceptions import ClientError
from quickbooks import QuickBooks
from intuitlib.client import AuthClient
from quickbooks.objects import *
from quickbooks.helpers import *
from collections import OrderedDict
from locale import *
from decimal import Decimal, getcontext
# warning! this won't work if we multiply
TWOPLACES = Decimal(10) ** -2
setlocale(LC_NUMERIC, '')

detail_map = OrderedDict([
    ("Pre-Discount Sales", ("1", 1)), #Sales
    ("Discounts", ("35", -1)), #Discounts
    # ("Register Audit (CID)", ("33", -1)), #Pay Out
    ("House Account", ("24", -1)),
    ("Online Gift Card", ("38", -1)),
    ("Gift Card", ("30", -1)),
    ("Online Credit Card", ("37", -1)),
    ("InStore Credit Card", ("28",-1)),
    ("Third Party", ("42", -1)),
    ("Gift Cards Sold", ("34", 1)),
    ("Sales Tax", ("15", 1)),
    ("Donations", ("36", 1)),
    ("Online CC Tips", ("32", 1)),
    ("CC Tips", ("32", 1))
])

gl_code_map = { "1700" : "1995", #security deposit
               "2400" : "6236", # Sales Tax Payable
               "4000" : "1301", # Sales (stouborn soda?)
               "5010" : "1301", # Food Other
               "5010.1" : "1301", # Bread
               "5010.2" : "1301", # Chips
               "5010.3" : "1301", # Cookies
               "5010.5" : "1301", # Meat
               "5010.6" : "1301", # Cheese
               "5020" : "1301", # Paper
               "5030" : "1301", # Beverages Other
               "5030.1" : "1301", # Beverages Fountain
               "5030.2" : "1301", # Beverages Bottles
               "5040" : "1301", # Produce
               "6243" : "6720", # Kitchen
               "6244" : "6730", # Kitchen - Gloves
               "6245" : "6720", # Kitchen - Cleaning Supplies
               "6293" : "5500", # Min Order Charge -> COGS - Delivery
               "8026" : "6236"} # Sales and Use Tax

gl_code_map_to_cogs = { "1700" : "1995", #security deposit
               "2400" : "6236", # Sales Tax Payable
               "4000" : "5102", # Sales (stouborn soda?)
               "5010" : "5200", # Food Other
               "5010.1" : "5201", # Bread
               "5010.2" : "5202", # Chips
               "5010.3" : "5203", # Cookies
               "5010.5" : "5204", # Meat
               "5010.6" : "5205", # Cheese
               "5020" : "5300", # Paper
               "5030" : "5100", # Beverages Other
               "5030.1" : "5101", # Beverages Fountain
               "5030.2" : "5102", # Beverages Bottles
               "5040" : "5400", # Produce
               "6243" : "6720", # Kitchen
               "6244" : "6730", # Kitchen - Gloves
               "6245" : "6720", # Kitchen - Cleaning Supplies
               "6293" : "5500", # Min Order Charge -> COGS - Delivery
               "8026" : "6236"} # Sales and Use Tax

account_ref = None

vendor = None

def lambda_handler(event, context):
    auth_client = refresh_session()

    client = QuickBooks(auth_client=auth_client,company_id="1401432085")

    return {
        'statusCode': 200,
        'body': get_secret()
    }

def update_royalty(year, month, payment_data):
    auth_client = refresh_session()

    client = QuickBooks(auth_client=auth_client,company_id="1401432085")

    supplier = Vendor.where("DisplayName like 'A Sub Above'")[0]
    lines = [ [wmc_account_ref(6335), "", payment_data["Royalty"] ],
              [wmc_account_ref(6105), "", payment_data["Advertising"] ],
              [wmc_account_ref(6107), "", payment_data["Media"] ],
              [wmc_account_ref(6106), "", payment_data["CoOp"] ]
            ]

    return sync_bill(supplier, str(year*100+month), datetime.date(year, month, calendar.monthrange(year, month)[1]), json.dumps(payment_data), lines)

def create_daily_sales(txdate, daily_report):
    auth_client = refresh_session()

    client = QuickBooks(auth_client=auth_client,company_id="1401432085")

    pattern = re.compile("\d+\.\d\d")

    existing_receipt = SalesReceipt.filter(TxnDate=qb_date_format(txdate))

    if len(existing_receipt) == 0:
        new_receipt = SalesReceipt()
    else :
        new_receipt = existing_receipt[0]
        # clear old lines
        new_receipt.Line.clear()


    new_receipt.TxnDate = qb_date_format(txdate)
    new_receipt.CustomerRef = Customer.all()[0].to_ref()

    line_num = 1
    amount_total = Decimal(0.0)
    for line_item, line_id in detail_map.items():
        line_text = daily_report[line_item]
        line = SalesItemLine()
        line.LineNum = line_num
        line.Description = "{} imported from ({})".format(
            line_item, daily_report[line_item])
        if daily_report[line_item]:
            if daily_report[line_item].startswith("N"):
                line.Amount = 0
            else:
                line.Amount = atof(daily_report[line_item].strip("$")) * line_id[1]
            amount_total += Decimal(line.Amount)
        else:
            line.Amount = 0
        line.SalesItemLineDetail = SalesItemLineDetail()
        item = Item.query(
            "select * from Item where id = '{}'".format(line_id[0]),client)[0]
        line.SalesItemLineDetail.ItemRef = item.to_ref()
        line.SalesItemLineDetail.ServiceDate = None
        new_receipt.Line.append(line)
        line_num += 1


    # Payin
    line = SalesItemLine()
    line.LineNum = line_num
    line_num += 1
    line.Description = daily_report["Payins"].strip()
    if line.Description.count('\n')>0:
        amount = Decimal(0)
        for payin_line in line.Description.split('\n')[1:]:
            amount = amount + Decimal(atof(pattern.search(payin_line).group()))
        line.Amount = amount.quantize(TWOPLACES)
        amount_total += amount
    else:
        line.Amount = 0
    line.SalesItemLineDetail = SalesItemLineDetail()
    item = Item.query(
        "select * from Item where id = '{}'".format(43),client)[0]
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
        line.Amount = (Decimal(atof(line.Description.split()[4])) - \
          Decimal(amount_total).quantize(TWOPLACES))
    else:
        line.Amount = 0
    line.SalesItemLineDetail = SalesItemLineDetail()
    item = Item.query(
        "select * from Item where id = '{}'".format(31),client)[0]
    line.SalesItemLineDetail.ItemRef = item.to_ref()
    line.SalesItemLineDetail.ServiceDate = None
    new_receipt.Line.append(line)

    new_receipt.PrivateNote = json.dumps(daily_report, indent=1)

    return new_receipt.save(qb=client)

def enter_online_cc_fee(year, month, payment_data):
    auth_client = refresh_session()

    client = QuickBooks(auth_client=auth_client,company_id="1401432085")

    supplier = Vendor.where("DisplayName like 'Jersey Mikes%'")[0]
    lines = [ [wmc_account_ref(6120), "", payment_data["Total Fees"] ] ]

    return sync_bill(supplier, str(year*100+month), datetime.date(year, month, calendar.monthrange(year, month)[1]), json.dumps(payment_data), lines)

def sync_bill(supplier, invoice_num, invoice_date, notes, lines):
    auth_client = refresh_session()

    client = QuickBooks(auth_client=auth_client,company_id="1401432085")

    # is this a credit
    if reduce(lambda x, y:x + atof(y[-1]), lines, 0.0) < 0.0:
        tx_type = VendorCredit
        item_sign = -1
    else:
        item_sign = 1
        tx_type = Bill

    # see if the invoice number already exists
    query = tx_type.filter(DocNumber=invoice_num)
    if len(query) == 0:
        #create the bill
        bill = tx_type()
        bill.DocNumber=invoice_num
    else:
        bill = query[0]

    bill.TxnDate = qb_date_format(invoice_date)

    bill.VendorRef = supplier.to_ref()

    bill.PrivateNote = notes

    if item_sign >0:
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
        line.Amount = Decimal(atof(bill_line[2])).quantize(TWOPLACES) * item_sign
        line.Description = bill_line[1]
        line_num += 1
        bill.Line.append(line)

    try:
        bill.save(qb=client)
    except Exception as ex:
        print(bill.to_json())
        print(ex)

def wmc_account_ref(acctNum):
    global account_ref
    if account_ref == None:
        auth_client = refresh_session()
        client = QuickBooks(auth_client=auth_client,company_id="1401432085")
        account_ref = dict(map(lambda x : (x.AcctNum, x.to_ref()),
             Account.all(max_results=1000)))
    return account_ref[str(acctNum)]

def account_ref_lookup(gl_account_code):
    global account_ref
    if account_ref == None:
        auth_client = refresh_session()
        client = QuickBooks(auth_client=auth_client,company_id="1401432085")
        account_ref = dict(map(lambda x : (x.AcctNum, x.to_ref()),
             Account.all(max_results=1000)))

    return account_ref[gl_code_map[gl_account_code]]

def vendor_lookup(gl_vendor_name):
    global vendor
    if vendor == None:
        auth_client = refresh_session()
        client = QuickBooks(auth_client=auth_client,company_id="1401432085")
        vendor = {
         'WNEPLS':
         Vendor.where("DisplayName like 'The Paper%'")[0],
         'PR-D&D':
         Vendor.where("DisplayName like 'D&D%'")[0],
         'PEPSI':
         Vendor.where("DisplayName like 'Pepsi%'")[0],
         'SYSLOS':
         Vendor.where("DisplayName like 'Sysco%'")[0]}
    return vendor[gl_vendor_name]

def refresh_session():
    s = json.loads(get_secret())

    auth_client = AuthClient(
    client_id=s['client_id'],
    client_secret=s['client_secret'],
    redirect_uri=s['redirect_url'],
    access_token= s['access_token'],
    refresh_token= s['refresh_token'],
    environment="production")

    # caution! invalid requests return {"error":"invalid_grant"} quietly
    auth_client.refresh()
    s['access_token'] = auth_client.access_token
    s['refresh_token'] = auth_client.refresh_token
    put_secret(json.dumps(s))
    QuickBooks.enable_global()
    return auth_client

secret_name = "prod/qbo"
region_name = "us-east-2"

# Create a Secrets Manager client
session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name
)

def get_secret():
    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return base64.b64decode(get_secret_value_response['SecretBinary'])

def put_secret(secret_string):
    put_secret_value_response = client.put_secret_value(
            SecretId=secret_name, SecretString=secret_string)

