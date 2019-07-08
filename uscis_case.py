import requests
from bs4 import BeautifulSoup
from datetime import date
from multiprocessing import Pool
import smtplib from email.MIMEMultipart 
import MIMEMultipart from email.MIMEBase 
import MIMEBase from email.MIMEText 
import MIMEText from email.Utils 
import COMMASPACE, formatdate from email 
import Encoders import os

URL = 'https://egov.uscis.gov/casestatus/mycasestatus.do'
# Important Notice: please limit your range size to 1000 receipts,
# larger number may cause uscis block your ip.
RECEIPT_NUM_RANGE = range(1990227366, 1990527366, 300)


def MakeRequest(case_id):
    return requests.post(URL, data = {'appReceiptNum': case_id})

# return [case_status, case_detail]
def GetStatusContentFromHtml(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    return [str(soup.findAll('h1')[0]).lstrip('<h1>').rstrip('</h1>'), str(soup.findAll('p')[0])]

def GetChangeDateFromCaseDetail(case_detail):
    year = int(case_detail.split(',')[1].strip())

    month_day = case_detail.split(',')[0][6:].split(' ')
    month = ParseMonth(month_day[0])
    day = int(month_day[1])

    return date(year, month, day)

def GetCaseNumberFromCaseDetail(case_detail):
    start = case_detail.find('YSC')
    return case_detail[start:(start+13)]


def sendMail(to, fro, subject, text, files=[],server="localhost"):
    msg = MIMEMultipart()     
    msg['From'] = fro     
    msg['To'] = COMMASPACE.join(to)     
    msg['Date'] = formatdate(localtime=True)     
    msg['Subject'] = subject
    msg.attach( MIMEText(text) )
    for file in files:
        part = MIMEBase('application' "octet-stream")
        part.set_payload( open(file,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                % os.path.basename(file))
        msg.attach(part)
    smtp = smtplib.SMTP(server)
    smtp.sendmail(fro, to, msg.as_string() )
    smtp.close()

def ParseMonth(word):
    word = word.lower()
    if word == 'january' or word == 'jan':
        return 1
    elif word == 'february' or word == 'feb':
        return 2
    elif word == 'march' or word == 'mar':
        return 3
    elif word == 'april' or word == 'apr':
        return 4
    elif word == 'may':
        return 5
    elif word == 'june' or word == 'jun':
        return 6
    elif word == 'july' or word == 'jul':
        return 7
    elif word == 'august' or word == 'aug':
        return 8
    elif word == 'september' or word == 'sep':
        return 9
    elif word == 'october' or word == 'oct':
        return 10
    elif word == 'november' or word == 'nov':
        return 11
    elif word == 'december' or word == 'dec':
        return 12
    else:
        return 0

def CompareStatus(case):
    file_name = 'case_status_' + case
    [case_number, case_status, change_date] = GetCaseStatus(case)
    with open(file_name, 'r+') as myfile:
        data = myfile.read()
        if case_status == data:
            return
        else:
            myfile.seek(0)
            myfile.write(case_status)
            myfile.truncate()

def GetCaseStatus(receipt):
    raw_html = MakeRequest(receipt).text
    [case_status, case_detail] = GetStatusContentFromHtml(raw_html)
    change_date = GetChangeDateFromCaseDetail(case_detail)
    case_number = GetCaseNumberFromCaseDetail(case_detail)
    return [case_number, case_status, change_date]

def UpdateCaseStatus(num_range):
    file_name = 'case_status_' + date.today().isoformat()
    with open(file_name, 'w') as of:
        print('receipt_num,case_status,change_date')
        for case in num_range:
            receipt = 'YSC' + str(case)
            print('Fetching Case Status: ' + receipt)
            [case_number, case_status, change_date] = GetCaseStatus(receipt)
            print(case_number + ',' + case_status + ',' + change_date.isoformat())

def UpdateCaseStatusAsync(num_range):
    pool = Pool()
    futures = []
    for case in num_range:
        receipt = 'YSC' + str(case)
        print('Fetching Case Status: ' + receipt)
        futures.append(pool.apply_async(GetCaseStatus, [receipt]))

    file_name = 'case_status_' + date.today().isoformat()
    with open(file_name, 'w') as of:
        for future in futures:
            res = future.get(timeout=10)
            print(res[0] + ',' + res[1] + ',' + res[2].isoformat())

def main():
    CompareStatus('YSC1990277366')

if __name__ == "__main__":
    main()
