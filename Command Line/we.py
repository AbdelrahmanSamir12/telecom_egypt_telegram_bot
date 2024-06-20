import requests
import json
import sqlite3
import argparse
from datetime import datetime
from sys import exit
# Database setup
db_file = 'we_data.db'

def create_db():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS credentials (
                        id INTEGER PRIMARY KEY,
                        number TEXT NOT NULL,
                        password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def get_credentials():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT number, password FROM credentials WHERE id=1')
    result = cursor.fetchone()
    conn.close()
    return result

def save_credentials(number, password):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('REPLACE INTO credentials (id, number, password) VALUES (1, ?, ?)', (number, password))
    conn.commit()
    conn.close()

def delete_credentials():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM credentials WHERE id=1')
    conn.commit()
    conn.close()
    print("your credentials deleted successfully, enter your new credentials")

def prompt_credentials():
    number = input("Enter your phone number: ")
    password = input("Enter your password: ")
    save_credentials(number, password)
    return number, password

def check_internet(url='http://www.google.com/', timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        return True if response.status_code == 200 else False
    except requests.ConnectionError:
        return False



    
# Command-line argument parsing
parser = argparse.ArgumentParser(description='Manage user credentials.')
parser.add_argument('--set-credentials', action='store_true', help='Set or update the phone number and password.')
parser.add_argument('--delete-credentials', action='store_true', help='delete the phone number and password.')
args = parser.parse_args()

# Initialize database
create_db()

if args.set_credentials:
    prompt_credentials()

if args.delete_credentials:
    delete_credentials()
    exit()

try: 
    credentials = get_credentials()
except:
    prompt_credentials()
    credentials = get_credentials()


if not credentials:
    credentials = prompt_credentials()

number, password = credentials
accountID = "FBB" + number[1:]

session = requests.Session()

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "channelId": "702",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "csrftoken": "",
    "delegatorSubsId": "",
    "Host": "my.te.eg",
    "isCoporate": "false",
    "isMobile": "false",
    "isSelfcare": "true",
    "languageCode": "en-US",
    "Origin": "https://my.te.eg",
    "Referer": "https://my.te.eg/echannel/",
    "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}


body = '{"acctId" : "%s","password" : "%s","appLocale": "en-US","isSelfcare": "Y","isMobile": "N","recaptchaToken": ""}' % (accountID, password)

loginURL = "https://my.te.eg/echannel/service/besapp/base/rest/busiservice/v1/auth/userAuthenticate"
# Fetching the login JWT (JSON Web Token) to use it to fetch login data
try:
    Login_Token_request = session.post(loginURL, headers=headers, data=body, verify=True)
    login_respond_data = json.loads(Login_Token_request.text)
    utoken = login_respond_data["body"]["utoken"]
    token = login_respond_data["body"]["token"]
    subId = login_respond_data["body"]["subscriber"]["subscriberId"]
    headers["csrftoken"] = token
    headers["u-token"] = utoken
except:
    if check_internet():
        print("Wrong Credentials or Telecom Egypt server is dowm \n use --set-credentials argument to update it")
    else:
        print("Check your internet Coneection")

    exit()

# Get quota data
units_url = "https://my.te.eg/echannel/service/besapp/base/rest/busiservice/cz/cbs/bb/queryFreeUnit"

body = '{"subscriberId": "%s"}' % subId
data_req = session.post(units_url, headers=headers, data=body, verify=True)
data = json.loads(data_req.text)

remaining = data["body"][0]["actualRemain"]
used = data["body"][0]["used"]
total = data["body"][0]["total"]
remainingDays = data["body"][0]["freeUnitBeanDetailList"][0]["remainingDaysForRenewal"]
percentage = "%.2f" % (used / total * 100)


we_message = f'Available      : {remaining} GB from {total} GB \nUsed           : {used} GB \nUsage percent  : {percentage} %\nRemaining days : {remainingDays} days'

print("___________________________")
print(f'Internet usage report for : {number}\n')
print(we_message)
print("time           : " + str(datetime.now().strftime("%H:%M %p")))
print("___________________________\n")
