import json
import datetime
import os
import calendar
import openpyxl
import boto3
import flexepos
from itertools import islice
from decimal import Decimal
from locale import LC_NUMERIC, atof, setlocale
from openpyxl.worksheet.dimensions import ColumnDimension, DimensionHolder
from openpyxl.utils import get_column_letter
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from wheniwork import WhenIWork
from ssm_parameter_store import SSMParameterStore
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from collections import defaultdict
from operator import itemgetter

WHENIWORK_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S %z"

# warning! this won't work if we multiply
TWOPLACES = Decimal(10) ** -2
setlocale(LC_NUMERIC, "")

def color_print(json_obj):
    print(highlight(json.dumps(json_obj,indent=2), JsonLexer(), TerminalFormatter()))
    return

class Tips:
    """ """
    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix="/prod")["wheniwork"]
        self._a = WhenIWork()
        self._a.login(self._parameters["user"], self._parameters["password"], self._parameters["key"])
        self._locations = {}
        self._stores = {}
        for location in self._a.get('/locations')['locations']:
            self._locations[location['id']] = location
            self._stores[location['name']] = location
        return

    def getTimes(self, stores, year_month_date, pay_period=0):
        if pay_period == 0 :
            span_dates = [
                datetime.date(year_month_date.year, year_month_date.month, 1),
                datetime.date(year_month_date.year, year_month_date.month, 
                calendar.monthrange(year_month_date.year, year_month_date.month)[1]) + datetime.timedelta(days=1)
            ]
        elif pay_period == 1:
            span_dates = [datetime.date(year_month_date.year, year_month_date.month, 1),
            datetime.date(year_month_date.year, year_month_date.month,16)] #not inclusive on end date
        elif pay_period == 2:
             span_dates = [
                datetime.date(year_month_date.year, year_month_date.month, 16),
                datetime.date(year_month_date.year, year_month_date.month, 
                calendar.monthrange(year_month_date.year, year_month_date.month)[1]) + datetime.timedelta(days=1)
            ]
        else:
            raise ValueError(f"pay_period must be set to 0 for entire month or 1 or 2 not {pay_period}")
        self._times = self._a.get('/times',params={"start":span_dates[0].isoformat(),"end":span_dates[1].isoformat()})
    
        rv = {}
        for store in stores:
            rv[store] = {}
            for time in list(filter(lambda rtime: rtime['location_id'] == self._stores[store]['id'], self._times['times'])):
                user_times = rv[store].get(time['user_id'], [] )
                user_times.append(time)
                rv[store][time['user_id']] = user_times

        return rv
    
    def emailTips(self, stores, tip_date):
        start_date = datetime.date(tip_date.year,tip_date.month,1)
        end_date = datetime.date(tip_date.year, tip_date.month, 
            calendar.monthrange(tip_date.year, tip_date.month)[1])
        parameters = SSMParameterStore(prefix="/prod")["email"]
        receiver_email = ['info@wagonermanagement.com']
        from_email = parameters["from_email"]
        subject = "Tip Spreadsheet for {}".format(tip_date.strftime("%m/%Y"))
        charset = "UTF-8"
        output = BytesIO()
        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)
        f = flexepos.Flexepos()  
        tip_totals = f.getTips(stores, start_date, end_date)
        times = self.getTimes(stores, datetime.date(start_date.year, start_date.month, 1))

        for store in stores:
            sheet = workbook.create_sheet(title=store)
            i = 3
            sheet.append(["{} - {}".format(store, tip_date.strftime("%B"))] + tip_totals[store][0])
            sheet.append(["=SUM(B2:K2)"] + tip_totals[store][1])
            for n in range(1,13):
                sheet.cell(2,n).number_format = '"$"#,##0.00_-'
            sheet.append(["Last Name", "First Name", "Hours", "Tip Share"])
            for user_times in times[store].values():
                user = self._a.get('/users/{}'.format(user_times[0]['user_id']))['user']

                first_name = user['first_name']
                last_name = user['last_name']
                sheet.append([last_name, first_name, 
                    sum(item['length'] for item in user_times),
                    '=$A$2 / SUM($C$4:$C$99) * $C{}'.format(i + 1)]
                )
                sheet.cell(i+1, 4).number_format = '"$"#,##0.00_-'
                i = i + 1
            
            sheet.auto_filter.ref = "A3:D{}".format(i)
            sheet.auto_filter.add_sort_condition("A3:A{}".format(i))
            dim_holder = DimensionHolder(worksheet=sheet)
            for col in range(sheet.min_column, sheet.max_column +1):
                dim_holder[get_column_letter(col)] = ColumnDimension(sheet, min=col, max=col, bestFit=True)
            sheet.column_dimensions = dim_holder
            
        workbook.save(output)

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = ", ".join(receiver_email)
        part = MIMEText('Attached is the spreadsheet\n\n')
        msg.attach(part)
        part = MIMEApplication(output.getvalue())
        part.add_header('Content-Disposition', 'attachment', filename='tips.xlsx')
        msg.attach(part)

        client = boto3.client('ses')
        client.send_raw_email(
            Source=msg['From'],
            Destinations=receiver_email,  ## passed in an array
            RawMessage={
            'Data':msg.as_string(),
            }
        )

    def getMissingPunches(self):
        times = self._a.get('/times',
            params= { "start": (datetime.date.today()-datetime.timedelta(days=20)).isoformat(),
                "end":(datetime.date.today()-datetime.timedelta(days=1)).isoformat() }
            )
        self._users = {}
        for user in times['users']:
            self._users[user['id']] = user
        return list(filter(lambda rtime: rtime['end_time'] is None, times['times']))

    def getMealPeriodViolations(self, stores, year_month_date, pay_period=0):
        times = self.getTimes(stores, year_month_date, pay_period)
        mpvs = []
        for store in stores:
            for user_times in times[store].values():
                user = self._a.get('/users/{}'.format(user_times[0]['user_id']))['user']

                first_name = user['first_name']
                last_name = user['last_name']
                hourly_rate = user['hourly_rate']
                if last_name == "Wagoner" and first_name == "Lillian":
                        last_name = "Nicholson"
                day_dict = defaultdict(list)
                for time in user_times:
                    day = datetime.datetime.strptime(time['start_time'], WHENIWORK_DATE_FORMAT).date()
                    day_dict[day].append(time)
                for day, day_times in day_dict.items():
                    day_hours = sum(i['length'] for i in day_times)
                    day_times[0]['first_name'] = first_name
                    day_times[0]['last_name'] = last_name 
                    
                    day_times[0]['store'] = store
                    day_times[0]['hourly_rate'] = hourly_rate
                    day_times[0]['day'] = day
                    if len(day_times)==1:
                        if day_hours > 6:
                            mpvs.append(day_times[0])
                    elif day_hours > 6:
                        if day_times[0]['length']>5:
                            mpvs.append(day_times[0])
                        # does not take into account 12 hour shifts
                        end_time = datetime.datetime.strptime(day_times[0]['end_time'], WHENIWORK_DATE_FORMAT)
                        next_time = datetime.datetime.strptime(day_times[1]['start_time'], WHENIWORK_DATE_FORMAT)
                        break_duration = next_time - end_time
                        if break_duration < datetime.timedelta(minutes=30):
                            print(f"WARNING: {day.isoformat()} {last_name}, {first_name} {str(break_duration)} break.")

        return sorted(mpvs, key=itemgetter('last_name','first_name'))

    def exportMealPeriodViolations(self, stores, year_month_date, pay_period=0):
        text_csv = []
        mpvs = self.getMealPeriodViolations(stores, year_month_date, pay_period)
        grouped = defaultdict(list)
        for mpv in mpvs:
            grouped[f"{mpv['last_name']}, {mpv['first_name']}"].append(mpv)

        text_csv.append("last_name,first_name,title,custom_earning_meal_period_violations,personal_note")
        for g in grouped.values():
            mpv = g[0]
            t= f"{mpv['last_name']},{mpv['first_name']}," +\
                "Crew (Primary)," +\
                f"{sum(item['hourly_rate'] for item in g)}," +\
                f"\"MPV {', '.join(list(str(item['day'].month) + '/' + str(item['day'].day) for item in g))}\""
            if pay_period == 0:
                t+= f",\"{mpv['store']}\""
            text_csv.append(t)
        return "\n".join(text_csv)

    def exportTipsTransform(self, tips_stream):
        text_csv = []
        workbook = openpyxl.load_workbook(tips_stream, data_only=True)
        text_csv.append("last_name,first_name,title,paycheck_tips")
        for sheet_name in workbook.get_sheet_names():
            worksheet = workbook.get_sheet_by_name(sheet_name)
            for row in islice(worksheet.rows,3, None):
                if row[3].value != None: #also test for zero
                    text_csv.append(f"{row[0].value},{row[1].value},Crew (Primary),{Decimal(row[3].value).quantize(TWOPLACES)}") 
        return "\n".join(text_csv)