import subprocess
import sys
from datetime import datetime
import time
import smtplib
import json

app_id = [""]


expiry_dates = []
key_ids = []

for app in app_id:
    time.sleep(5)
    result_data = subprocess.check_output(['powershell', 'az',
                                           f'ad app credential list --id {app}'' --query "[].{KEY:keyId, END:endDateTime}" --output json'],
                                          shell=True, text=True)
    json_date = json.loads(result_data)

    for data in json_date:
        key = data["KEY"]
        date = data["END"]
        expiry_dates.append(date)
        key_ids.append(key)

    today_date = datetime.today().strftime("%Y-%m-%d")
    current_date = datetime.strptime(today_date, "%Y-%m-%d")

    for get_date in expiry_dates:
        date = get_date.split('T')
        date_hours = date[0]
        required_date = datetime.strptime(date_hours, "%Y-%m-%d")

    time_difference = required_date - current_date
    difference_days = time_difference.days
    print(difference_days)

    if difference_days < 30:

        print("Secret is expired renew it")

        smtp_server = ""
        smtp_port = 
        username = ""
        password = ""

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        server.login(user=username, password=password)

        from_addr = ""
        to_addr = ["",""]

        if difference_days < 0:

            body = f"The Azure AAD has expired from past {difference_days} days. \n APP_ID: {app} \n SECRET_KEYID: {key} "
            subject = "AAD Secret has Expired"
            message = f"From: {from_addr}\nTo: {to_addr}\nSubject: {subject}\n\n{body}"

            server.sendmail(from_addr, to_addr, message)
            server.quit()
            print("Message has sent Successfully")

        else:

            body = f"The Azure AAD will Expire in {difference_days} days from Now. \n APP_ID: {app} \n SECRETKEY_ID: {key} "
            subject = f"AAD Secret Will Expire in {difference_days} days"
            message = f"From: {from_addr}\nTo: {to_addr}\nSubject: {subject}\n\n{body}"

            server.sendmail(from_addr, to_addr, message)
            server.quit()
            print("message has sent successfully")

    if required_date > current_date:
        print(f"The Expiry date for  AAD ID: '{app}' with Secret ID: '{key}' are still above 30 days ")
