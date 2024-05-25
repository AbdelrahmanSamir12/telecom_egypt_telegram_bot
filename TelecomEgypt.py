import requests
import json
import schedule
import telebot
from decouple import config
import time
from threading import Thread



"""
you can use this class to fecth internet usage data without needing a 
telegram bot
"""
class WE_API():
    def __init__(self,login_phone,password):

        self.login_phone = login_phone
        self.password = password
        self.session = requests.Session()


    def fetch_data(self):
        number = self.login_phone
        accountID = "FBB" + number[1:] 

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

        body = '{"acctId" : "%s","password" : "%s","appLocale": "en-US","isSelfcare": "Y","isMobile": "N","recaptchaToken": ""}' %(accountID, self.password)

        loginURL = "https://my.te.eg/echannel/service/besapp/base/rest/busiservice/v1/auth/userAuthenticate"
        # fetching the a login jwt "JASON web token" to use it to fetch login data
        Login_Token_request = self.session.post(loginURL, headers=headers, data = body, verify=True)
        login_respond_data = json.loads(Login_Token_request.text)

        utoken = login_respond_data["body"]["utoken"]
        token = login_respond_data["body"]["token"]
        subId = login_respond_data["body"]["subscriber"]["subscriberId"]
        headers["csrftoken"] = token
        headers["u-token"] = utoken



        #get internet subscrebtion data 
        units_url = "https://my.te.eg/echannel/service/besapp/base/rest/busiservice/cz/cbs/bb/queryFreeUnit"

        body = ' {"subscriberId": "%s"}' %(subId)  
        data_req = self.session.post(units_url, headers= headers , data = body, verify=True)
        data = json.loads(data_req.text)

        remaining = data["body"][0]["actualRemain"]
        used = data["body"][0]["used"]
        total = data["body"][0]["total"]
        remainingDays = data["body"][0]["freeUnitBeanDetailList"][0]["remainingDaysForRenewal"]
        percentage ="%.2f" % (used / total * 100)
        responde = {
            "available" : remaining,
            "total" : total,
            "used" : used,
            "percentage" : percentage,
            "remaining": remainingDays
        }
        return responde


class TelegramBot():
    def __init__(self, api_token, login_phone, password, telegram_id):
        self.api_token = api_token
        self.telegram_id = telegram_id
        self.login_phone = login_phone
        self.password = password
        self.bot = telebot.TeleBot(api_token)
        self.WeDataFetcher = WE_API(login_phone,password)

    def send_summary(self, data):

        # Handling sending the Summary massege the the telegram account
        we_message = f'Available : {data["available"]} GB from {data["total"]} GB \n Used : {data["used"]} GB \nUsage percentage : {data["percentage"]} %\nRemaining days : {data["remaining"]} days'
        print(we_message)
        self.bot.send_message(self.telegram_id, we_message)
        

    def check_and_send(self):

        # Initiating communication with the API, retrieving usage information, and subsequently forwarding it to the user.
        data = self.WeDataFetcher.fetch_data()
        self.send_summary(data)

    def scheduled(self):

        #Managing the automated process of sending scheduled usage summaries to the user.
        schedule.every(2).hours.do(self.check_and_send)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def StartTelegramBot(self):

        #handles the whole proccess of the bot
        self.check_and_send()
        @self.bot.message_handler(commands=["check"])
        def check(message):
            self.check_and_send()

        """
        Implementing multi-threading to enable the script to simultaneously manage user commands
        and scheduled usage summary sent to the user.
        """
        send_thread = Thread(target=self.scheduled)
        send_thread.start()
        
        command_thread = Thread(target=self.bot.polling)
        command_thread.start()

    
    


def main():
  
    telegram_user_id = int(config('telegram_id'))
    telegram_bot_token = config('Token')
    login_phone = config('LoginPhone')
    we_account_password = config('Password') 

    # Fetching internet usage data without using a Telegram bot
    we_account_data_fetcher = WE_API(login_phone,we_account_password)
    we_account_data_fetcher.fetch_data()

    # Using the Telegram bot
    telegram = TelegramBot(telegram_bot_token,login_phone,we_account_password,telegram_user_id)
    telegram.StartTelegramBot()





if __name__ == "__main__":
    main()


