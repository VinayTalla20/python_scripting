import os
import re
import smtplib
import pandas as pd
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from azure.identity import ClientSecretCredential

# credential = DefaultAzureCredential()
# manged_credential = ManagedIdentityCredential(client)

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CRON_PASSWD = os.getenv("CRON_PASSWD")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")
REQUIRED_MAILS = os.getenv("REQUIRED_MAILS")
CLUSTER_ENV = os.getenv("CLUSTER_ENV")


credential = ClientSecretCredential(tenant_id=f"{TENANT_ID}",
                                    client_id=f"{CLIENT_ID}",
                                    client_secret=f"{CLIENT_SECRET}")

client = LogsQueryClient(credential)

container_id_Query = """ContainerLog | where LogEntry matches regex ".Exception:" | where TimeGenerated > ago(24h)| summarize count() by ContainerID | project ContainerID """

required_container_ids = []
final_timeGenerated = []
final_container_ids = []
required_time = None
before_time = None
final_pod_names = []
filename = None
csv_filenames = []
extracted_logentries = []
required_logentries = []
extractedLogTime = []
SEND_MAILS = []

# To get list of mails
mail = REQUIRED_MAILS.split(",")

for to_mails in mail:
    SEND_MAILS.append(to_mails)


# smtp connections

smtp_server = "smtp.office365.com"
smtp_port = 587
username = ""
password = f"{CRON_PASSWD}"
from_addr = ""
to_addr = SEND_MAILS
subject = f"SmartConx {CLUSTER_ENV} Exceptions"

body = "Hi Team,\n\n Below are the pods with exceptions from the last 24 hours. Please find the attached logs for further analysis.\n"

body += "\nPOD's with Exceptions:\n \n"

try:
    response = client.query_workspace(
        workspace_id=f"{WORKSPACE_ID}",
        query=container_id_Query,
        timespan=None

    )
    if response.status == LogsQueryStatus.PARTIAL:
        error = response.partial_error
        data = response.partial_data
        print(error)
    elif response.status == LogsQueryStatus.SUCCESS:
        data = response.tables
    for table in data:
        df = pd.DataFrame(data=table.rows, columns=table.columns)
        # Set display options to show all rows and columns
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        pd.set_option("display.max_colwidth", None)

    for container_ids in df.values:
        for container_id in container_ids:
            required_container_ids.append(container_id)


except HttpResponseError as err:
    print("Something fatal happened:")
    print(err)

# method  to get podname

def podname(container_id):
    pod_name = None

    Pod_Query = f""" KubePodInventory | where ContainerID contains "{container_id}" | summarize count() by Name | project Name"""

    try:
        response = client.query_workspace(
            workspace_id=f"{WORKSPACE_ID}",
            query=Pod_Query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for pod_table in data:
            pod_details = pd.DataFrame(data=pod_table.rows, columns=pod_table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            for pod in pod_details["Name"]:
                pod_name = pod


    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)

    return pod_name


for get_container_id in required_container_ids:

    Time_Generation_Query = f"""ContainerLog | where LogEntry matches regex ".Exception:" | where ContainerID contains "{get_container_id}" | where TimeGenerated > ago(24h) | sort by TimeGenerated asc | distinct LogEntry  | project LogEntry """

    try:
        response = client.query_workspace(
            workspace_id=f"{WORKSPACE_ID}",
            query=Time_Generation_Query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            time_generation_details = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            logentry = time_generation_details["LogEntry"]

            # deduplicating elements in Array by spliting string at "Exception:"
            for all_logentries in logentry.values:
                # print("Log Entry",all_logentries)
                result = re.search(r'(\S+Exception:)', all_logentries)
                if result:
                    extracted_string = result.group(0)

                    extracted_logentries.append(extracted_string)

        # Deduplicating Extracted LogEntries
        for logentries in extracted_logentries:
            if logentries not in required_logentries:
                required_logentries.append(logentries)
        extracted_logentries.clear()
        # print("Finally after deDuplicating", required_logentries, "Array length", len(required_logentries))

        # To get Time Generation for Specific Log

        for pass_logentry in required_logentries:

            Exception_Query = f"""ContainerLog | where LogEntry contains "{pass_logentry}" | where ContainerID contains "{get_container_id}" | where TimeGenerated > ago(24h) | sort by TimeGenerated asc | take 1 | project TimeGenerated"""

            try:
                response = client.query_workspace(
                    workspace_id=f"{WORKSPACE_ID}",
                    query=Exception_Query,
                    timespan=None

                )
                if response.status == LogsQueryStatus.PARTIAL:
                    error = response.partial_error
                    data = response.partial_data
                    print(error)
                elif response.status == LogsQueryStatus.SUCCESS:
                    data = response.tables
                for table in data:
                    Exception_time_generation_details = pd.DataFrame(data=table.rows, columns=table.columns)
                    # Set display options to show all rows and columns
                    pd.set_option("display.max_rows", None)
                    pd.set_option("display.max_columns", None)
                    pd.set_option("display.width", None)
                    pd.set_option("display.max_colwidth", None)

                    for logtime in Exception_time_generation_details["TimeGenerated"]:
                        extractedLogTime.append(logtime)

                        required_time = str(logtime)

                        required_time = required_time.split('.')[0]
                        required_time = datetime.strptime(required_time, '%Y-%m-%d %H:%M:%S') + timedelta(seconds=10)
                        required_time.strftime('%Y-%m-%d %H:%M:%S')

                        # print("Required time", required_time)

                        before_time = datetime.strptime(str(required_time), '%Y-%m-%d %H:%M:%S') - timedelta(minutes=1)
                        before_time.strftime('%Y-%m-%d %H:%M:%S')

                        # print("Time before 1 minute", before_time)

                # get POD names using ContainerID's and calling podname method

                required_podName = podname(container_id=f"{get_container_id}")

                now = datetime.now().strftime("%Y-%m-%d")
                filename = f"{required_podName}-Exceptions_{now}.txt"
                # print("file name", filename)

                # To get Logs for Specific Exception in the Time Frame of 1 minute

                container_Logs_Query = f"""ContainerLog | where ContainerID contains "{get_container_id}" | where TimeGenerated between (datetime("{before_time}") .. datetime("{required_time}")) | project LogEntry """

                try:
                    response = client.query_workspace(
                        workspace_id=f"{WORKSPACE_ID}",
                        query=container_Logs_Query,
                        timespan=None

                    )
                    if response.status == LogsQueryStatus.PARTIAL:
                        error = response.partial_error
                        data = response.partial_data
                        print(error)
                    elif response.status == LogsQueryStatus.SUCCESS:
                        data = response.tables
                    for table in data:
                        container_log_details = pd.DataFrame(data=table.rows, columns=table.columns)
                        # Set display options to show all rows and columns
                        pd.set_option("display.max_rows", None)
                        pd.set_option("display.max_columns", None)
                        pd.set_option("display.width", None)
                        pd.set_option("display.max_colwidth", None)

                        print(
                            f"Logs From {get_container_id} and {required_podName} for Log Entry {pass_logentry} are stored in {filename} from {before_time} to {required_time}")
                        container_log_details.to_csv(filename, mode='a', index=False,
                                                     header=not os.path.exists(filename))

                except HttpResponseError as err:
                    print("Something fatal happened:")
                    print(err)

            except HttpResponseError as err:
                print("Something fatal happened:")
                print(err)

        bullet_list = "\n".join([f"- {required_podName}   {required_logentries} \n"])
        body += bullet_list
        required_logentries.clear()
        csv_filenames.append(filename)

    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


# Email configuration


body += "\n\nThanks,\nDevOps Team"

# Create a multipart message
message = MIMEMultipart()
message["From"] = from_addr
message["To"] = ", ".join(to_addr)
message["Subject"] = subject

files = csv_filenames

# Attach the CSV file
for csv_file in files:
    with open(csv_file, "rb") as file:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(file.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename= {csv_file}")
    message.attach(part)

# Attach the email body
message.attach(MIMEText(body, "plain"))

# # Send the email
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(user=username, password=password)
    server.send_message(message)

print("Email with attachment sent successfully.")
