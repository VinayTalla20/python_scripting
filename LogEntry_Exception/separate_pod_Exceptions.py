import os
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

credential = ClientSecretCredential(tenant_id="",
                                    client_id="",
                                    client_secret="")

client = LogsQueryClient(credential)
container_id_Query = """ContainerLog | where LogEntry matches regex ".Exception:" | take 15 | where TimeGenerated > ago(24h)| project ContainerID """

required_container_ids = []
final_timeGenerated = []
final_container_ids = []
deDuplicated_container_ids = []
required_time = None
final_pod_names = []
filename = None
csv_filenames = []

try:
    response = client.query_workspace(
        workspace_id="d89c4a69-a664-433d-9d78-d8f5e3228e65",
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

        # print("Log Details")
    for container_ids in df.values:
        for container_id in container_ids:
            required_container_ids.append(container_id)

    # deDuplicating containers ids Array
    for id in required_container_ids:
        if id not in deDuplicated_container_ids:
            deDuplicated_container_ids.append(id)
    print(deDuplicated_container_ids)

except HttpResponseError as err:
    print("Something fatal happened:")
    print(err)

# To get TImeGenerated for specific container Ids

for get_container_id in deDuplicated_container_ids:
    Time_Generation_Query = f"""ContainerLog | where LogEntry matches regex ".Exception:" | where ContainerID contains "{get_container_id}" | where TimeGenerated > ago(24h)| sort by TimeGenerated asc| take 1 | project TimeGenerated """

    try:
        response = client.query_workspace(
            workspace_id="d89c4a69-a664-433d-9d78-d8f5e3228e65",
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

            print("Time Generation Details")
            print(time_generation_details)
            for time in time_generation_details.values:
                for final_time in time:
                    required_time = str(final_time)

    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)

    required_time = required_time.split('.')[0]
    required_time = datetime.strptime(required_time, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=1)
    required_time.strftime('%Y-%m-%d %H:%M:%S')
    print("Required time", required_time)
    before_time = datetime.strptime(str(required_time), '%Y-%m-%d %H:%M:%S') - timedelta(minutes=5)
    before_time.strftime('%Y-%m-%d %H:%M:%S')
    print("time before 5 minutes")
    print(before_time)

    # for get_container_id in deDuplicated_container_ids:
    print(f"Getting logs from {get_container_id}")
    print(f"get logs between {before_time} to {required_time}")

    Pod_Query = f""" KubePodInventory | where ContainerID contains "{get_container_id}" | summarize count() by Name | project Name"""

    try:
        response = client.query_workspace(
            workspace_id="d89c4a69-a664-433d-9d78-d8f5e3228e65",
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

            print("pod Details")
            print(pod_details.values)
            for pod_name in pod_details.values:
                for final_name in pod_name:
                    final_pod_names.append(final_name)
                    print(final_pod_names)
                    now = datetime.now().strftime("%Y-%m-%d")
                    filename = f"{final_name}-Exceptions_{now}.csv"
                    print("File Name:", filename)
                    csv_filenames.append(filename)
                    print("Total Files created:", csv_filenames)

    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)

    container_Logs_Query = f"""ContainerLog | where ContainerID contains "{get_container_id}" | where TimeGenerated between (datetime("{before_time}") .. datetime("{required_time}")) | project LogEntry """

    try:
        response = client.query_workspace(
            workspace_id="d89c4a69-a664-433d-9d78-d8f5e3228e65",
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

            print("Log Details")
            print(container_log_details)

            container_log_details.to_csv(filename, index=False)
            print(f"Query results saved to '{filename}'")

    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


# Email configuration

smtp_server = "smtp.office365.com"
smtp_port = 587
username = ""
password = ""
from_addr = ""
to_addr = [""]
subject = "Exceptions Mail"
body = "The Log Entry Exceptions from the last 24 hours.\nCluster: SmartConx-Dev"

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

# Send the email
with smtplib.SMTP(smtp_server, smtp_port) as server:
    server.starttls()
    server.login(user=username, password=password)
    server.send_message(message)

print("Email with attachment sent successfully.")
