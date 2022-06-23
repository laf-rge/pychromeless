import calendar
import datetime
import json
import os
import boto3
import crunchtime
import qb
from ubereats import UberEats
from doordash import Doordash
from grubhub import Grubhub
from flexepos import Flexepos
from ssm_parameter_store import SSMParameterStore
from functools import partial

if os.environ.get("AWS_EXECUTION_ENV") is not None:
    import chromedriver_binary

stores = ['20025', '20358']


def third_party_deposit_handler(*args, **kwargs):
    start_date = datetime.date.today() - datetime.timedelta(days=28)
    end_date = datetime.date.today()
    # start_date = datetime.date(2022, 4, 1)
    results = []
    try:
        d = Doordash()
        results.extend(d.get_payments(stores, start_date, end_date))
        u = UberEats()
        results.extend(u.get_payments(stores, start_date, end_date))
        g = Grubhub()
        results.extend(g.get_payments(start_date, end_date))
    finally:
        for result in results:
            qb.sync_third_party_deposit(*result)


def invoice_sync_handler(*args, **kwargs):
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    ct = crunchtime.Crunchtime()
    ct.process_gl_report(stores)
    ct.process_inventory_report(stores, yesterday.year, yesterday.month)
    return {"statusCode": 200, "body": "Success"}


def daily_sales_handler(*args, **kwargs):
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
    receiver_email = parameters["receiver_email"]
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
    message += "\nThanks!\nJosiah (aka The Robot)"

    response = client.send_email(Destination={
        'ToAddresses': [
        receiver_email,
        ],
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

    return {"statusCode": 200, "body": json.dumps(message)}
