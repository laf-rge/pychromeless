import calendar
import datetime
import json
import os
import smtplib
import ssl
from functools import partial

import crunchtime
import qb
from flexepos import Flexepos
from ssm_parameter_store import SSMParameterStore

if os.environ.get("AWS_EXECUTION_ENV") is not None:
    import chromedriver_binary

def invoice_sync_handler(*args, **kwargs):
    ct = crunchtime.Crunchtime()
    ct.process_gl_report()
    return {
        'statusCode':200,
        'body': 'Success'
    }

def daily_sales_handler(*args, **kwargs):
    txdates = [datetime.date.today() - datetime.timedelta(days=1)]
    #txdates = [datetime.date(2021,3,14)]
    #txdates = map(partial(datetime.date,2021,3),range(29,31))

    dj = Flexepos()
    for txdate in txdates:
        retry = True
        while (retry):
            try:
                journal = dj.getDailySales(["20025"],txdate)
                qb.create_daily_sales(txdate, journal)
                print(txdate)
                retry = False
            except Exception:
                print("error "+str(txdate))
                retry = True
    payment_data = dj.getOnlinePayments(["20025"], txdate.year, txdate.month)
    qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data)
    royalty_data = dj.getRoyaltyReport(["20025"], datetime.date(txdate.year, txdate.month, 1),
         datetime.date(txdate.year, txdate.month, calendar.monthrange(txdate.year, txdate.month)[1]))
    qb.update_royalty(txdate.year, txdate.month, royalty_data)
    return {
        'statusCode':200,
        'body': 'Success'
    }

def online_cc_fee(*args, **kwargs):
    txdate = datetime.date.today() - datetime.timedelta(days=1)

    dj = Flexepos()
    payment_data = dj.getOnlinePayments(["20025"], txdate.year, txdate.month)
    qb.enter_online_cc_fee(txdate.year, txdate.month, payment_data["20025"])
    return {
        'statusCode':200,
        'body': 'Success'
    }

def daily_journal_handler(event, context):
    parameters = SSMParameterStore(prefix='/prod')['email']
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    port = 465
    password = parameters['password']
    user = parameters['user']
    receiver_email = parameters['receiver_email']
    from_email = parameters['from_email']
    smtp_server = parameters['smtp_server']

    context = ssl.create_default_context()

    dj = Flexepos()
    drawer_opens = dict()
    drawer_opens = dj.getDailyJournal(["20025","20089","20128","20210","20240"],
                                      yesterday.strftime("%m%d%Y"))
    message = """\
From: {}
To: {}
Subject: Cash Drawer Open Report {}


Cash Drawer Open Report\n\n""".format(from_email, receiver_email, yesterday.strftime("%m/%d/%Y"))

    for store, journal in drawer_opens.items():
        message += "{}: {}\n""".format(store, journal.count("Cash Drawer Open"))
    message += "\n\nThanks!\n"

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(user, password)
        server.sendmail(user, receiver_email, message)
        print(message)

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }
