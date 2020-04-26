import datetime
import json
import qb
import smtplib, ssl
import crunchtime
from flexepos import Flexepos
from ssm_parameter_store import SSMParameterStore

def invoice_sync_handler(*args, **kwargs):
    ct = crunchtime.Crunchtime()
    ct.process_gl_report()
    return {
        'statusCode':200,
        'body': 'Success'
    }

def daily_sales_handler(*args, **kwargs):
    txdate = datetime.date.today() - datetime.timedelta(days=1)

    dj = Flexepos()
    journal = dj.getDailySales(["20025"],txdate)
    qb.create_daily_sales(txdate, journal["20025"])

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
