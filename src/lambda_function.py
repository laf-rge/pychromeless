import calendar
import datetime
import json
import os
import boto3
import crunchtime
import qb
import base64
import email
import io
from tips import Tips
from ubereats import UberEats
from doordash import Doordash
from grubhub import Grubhub
from flexepos import Flexepos
from ssm_parameter_store import SSMParameterStore
from functools import partial
from operator import itemgetter

if os.environ.get("AWS_EXECUTION_ENV") is not None:
    import chromedriver_binary

stores = ['20025', '20358']


def third_party_deposit_handler(*args, **kwargs):
    start_date = datetime.date.today() - datetime.timedelta(days=28)
    end_date = datetime.date.today()
    # start_date = datetime.date(2022, 4, 1)
    results = []
    try:
        dj = Flexepos()
        results.extend(dj.getGiftCardACH(stores, start_date, end_date))
        d = Doordash()
        results.extend(d.get_payments(stores, start_date, end_date))
        u = UberEats()
        results.extend(u.get_payments(stores, start_date, end_date))
        g = Grubhub()
        results.extend(g.get_payments(start_date, end_date))
    finally:
        for result in results:
            qb.sync_third_party_deposit(*result)
            print(result)


def invoice_sync_handler(*args, **kwargs):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    ct = crunchtime.Crunchtime()
    ct.process_gl_report(stores)
    if yesterday.day < 6:
        last_month = datetime.date.today() - datetime.timedelta(days=7)
        ct.process_inventory_report(stores, last_month.year, last_month.month)
        #ct.process_inventory_report(stores, 2023, 1)
    else:
        ct.process_inventory_report(stores, yesterday.year, yesterday.month)
    return {"statusCode": 200, "body": "Success"}


def daily_sales_handler(*args, **kwargs):
    event = {}
    if args != None and len(args)>0:
        event = args[0]
    if 'year' in event:
        txdates = [ datetime.date(
            year = int(event['year']),
            month = int(event['month']),
            day = int(event['day']))
        ]
    else:
        txdates = [datetime.date.today() - datetime.timedelta(days=1)]
    # txdates = [datetime.date(2022,4,15)]
    # txdates = map(partial(datetime.date, 2022, 4), range(6, 31))

    dj = Flexepos()
    for txdate in txdates:
        retry = 5
        while retry:
            try:
                journal = dj.getDailySales(stores, txdate)
                qb.create_daily_sales(txdate, journal)
                print(txdate)
                retry = 0
            except Exception as ex:
                print("error " + str(txdate))
                print(ex)
                retry -= 1
    payment_data = dj.getOnlinePayments(stores, txdate.year, txdate.month)
    qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data)
    royalty_data = dj.getRoyaltyReport(
        'wmc',
        datetime.date(txdate.year, txdate.month, 1),
        datetime.date(
            txdate.year, txdate.month, calendar.monthrange(txdate.year, txdate.month)[1]
        ),
    )
    qb.update_royalty(txdate.year, txdate.month, royalty_data)
    return {"statusCode": 200, "body": "Success"}


def online_cc_fee(*args, **kwargs):
    txdate = datetime.date.today() - datetime.timedelta(days=1)

    dj = Flexepos()
    payment_data = dj.getOnlinePayments(stores, txdate.year, txdate.month)
    qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data)
    return {"statusCode": 200, "body": "Success"}


def daily_journal_handler(*args, **kwargs):
    parameters = SSMParameterStore(prefix="/prod")["email"]
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    receiver_emails = parameters["receiver_email"].split(', ')
    from_email = parameters["from_email"]
    subject = "Daily Journal Report {}".format(yesterday.strftime("%m/%d/%Y"))
    charset = "UTF-8"

    dj = Flexepos()
    drawer_opens = dict()
    drawer_opens = dj.getDailyJournal(
        stores, yesterday.strftime("%m%d%Y")
    )

    client = boto3.client('ses')
    message = "Wagoner Management Corp.\n\nCash Drawer Opens:\n"

    for store, journal in drawer_opens.items():
        message = "{}{}: {}\n" "".format(
            message, store, journal.count("Cash Drawer Open")
        )

    message += "\n\nMissing Punches:\n"

    t = Tips()
    for time in t.getMissingPunches():
        user = t._users[time['user_id']]
        message = "{}{}, {} : {} - {}\n".format(message,
            user['last_name'], user['first_name'],
            t._locations[time['location_id']]['name'],
            time['start_time']
        )
    message += "\n\nMeal Period Violations:\n"
    for item in sorted(t.getMealPeriodViolations(stores, yesterday), key=itemgetter('store', 'start_time')):
            message += (f"MPV {item['store']} {item['last_name']}, {item['first_name']}, {item['start_time']}\n")
    message += "\n\nThanks!\nJosiah (aka The Robot)"

    response = client.send_email(Destination={
        'ToAddresses':  receiver_emails,
        },
        Message={
        'Body': {
        #'Html': {
        #'Charset': charset,
        #'Data': BODY_HTML,
        #},
        'Text': {
        'Charset': charset,
        'Data': message,
        },
        },
        'Subject': {
        'Charset': charset,
        'Data': subject,
        },
        },
        Source=from_email,
        # # If you are not using a configuration set, comment or delete the
        # # following line
        # ConfigurationSetName=CONFIGURATION_SET,
        )

    return {"statusCode": 200, "body": response}

def email_tips_handler(*args, **kwargs):
    event = {}
    if len(args) == 2 :
        event = args[0]
    if 'year' in event:
        txdate = datetime.date(
            int(event['year']),
            int(event['month']),
            int(event['day']))
    else:
        txdate = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    retries = 1
    while retries > 0:
        try:
            t = Tips()
            t.emailTips(stores, txdate)
            retries = 0
        except Exception as ex:
            print(ex)
        finally:
            retries = retries-1
            if retries == 0:
                raise ex

def jls_extract_def(event):
    # decoding form-data into bytes
    post_data = base64.b64decode(event["body"])
    # fetching content-type
    try:
        content_type = event["headers"]["Content-Type"]
    except:
        content_type = event["headers"]["content-type"]
    # concate Content-Type: with content_type from event
    ct = "Content-Type: " + content_type + "\n"
    
    # parsing message from bytes
    msg = email.message_from_bytes(ct.encode() + post_data)
    
    # checking if the message is multipart
    print("Multipart check : ", msg.is_multipart())
    multipart_content = {}
    # if message is multipart
    if msg.is_multipart():
        
        # retrieving form-data
        for part in msg.get_payload():
            # checking if filename exist as a part of content-disposition header
            if part.get_filename():
                # fetching the filename
                file_name = part.get_filename()
            print(part.get_content_type())
            multipart_content[
                part.get_param("name", header="content-disposition")
            ] = part.get_payload(decode=True)
    return multipart_content


def transform_tips_handler(*args, **kwargs):
    csv = ""
    try:
        event = {}
        if args != None and len(args)==2:
            event = args[0]
            context = args[1]
        tips_stream = None
        
        if 'excel' in kwargs:
            tips_stream = open("tips-aug.xlsx", "rb")
        else:
            multipart_content = jls_extract_def(event) 
            tips_stream = io.BytesIO(multipart_content.get("file", None))
        t = Tips()
        csv = t.exportTipsTransform(tips_stream)
    except Exception as e:
        print(e)
        return {"statusCode": 400, "body": str(e)}
    return {"statusCode": 200, 'headers': { "Content-type": "text/csv",
        'Content-disposition': 'attachment; filename=gusto_upload.csv'},"body": csv}

def get_mpvs_handler(*args, **kwargs):
    csv = ""
    year = datetime.date.today().year
    month = datetime.date.today().month
    pay_period = 2
    
    try:
        event = {}
        if args != None and len(args)==2:
            event = args[0]
            context = args[1]
        multipart_content = jls_extract_def(event)
        if 'year' in multipart_content:
            try:
                year = int(multipart_content['year'])
                month = int(multipart_content['month'])
                pay_period = int(multipart_content['pay_period'])
            except Exception as ex:
                return {"statusCode": 400, "body": str(e)}
        t = Tips()
        csv = t.exportMealPeriodViolations(stores, datetime.date(year, month, 5), pay_period)
    except Exception as e:
        print(e)
        return {"statusCode": 400, "body": str(e)}
    return {"statusCode": 200, 'headers': { "Content-type": "text/csv",
        'Content-disposition': 'attachment; filename=gusto_upload_tips.csv'},"body": csv}