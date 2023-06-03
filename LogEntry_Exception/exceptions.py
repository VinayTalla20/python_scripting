import os
import smtplib
import pandas as pd
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from azure.identity import ClientSecretCredential

# credential = DefaultAzureCredential()
# manged_credential = ManagedIdentityCredential(cleint)

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CRON_PASSWD = os.getenv("CRON_PASSWD")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")


credential = ClientSecretCredential(tenant_id=f"{TENANT_ID}",
                                    client_id=f"{CLIENT_ID}",
                                    client_secret=f"{CLIENT_SECRET}")

client = LogsQueryClient(credential)
query = """ContainerLog | where LogEntry matches regex ".Exception" | where TimeGenerated > ago(24h)| project LogEntry, ContainerID"""

# start_time = datetime(2023, 5, 6, tzinfo=timezone.utc)
# end_time = datetime(2023, 5, 7, tzinfo=timezone.utc)

try:
    response = client.query_workspace(
        workspace_id=f"{WORKSPACE_ID}",
        query=query,
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

        now = datetime.now().strftime("%Y-%m-%d")
        filename = f"Exceptions_{now}.csv"
        df.to_csv(filename, index=False)
        print(f"Query results saved to '{filename}'")

        # Email configuration
        smtp_server = "smtp.office365.com"
        smtp_port = 587
        username = "cron@italentdigital.com"
        password = f"{CRON_PASSWD}"
        from_addr = "cron@italentdigital.com"
        to_addr = ["vinayt@italentdigital.com", "bhanub@italentdigital.com", "yeshwanth@italentdigital.com"]
        subject = "Exceptions Mail"
        body = "The Log Entry Exceptions from the last 24 hours.\nCluster: SmartConx-Dev"

        # Create a multipart message
        message = MIMEMultipart()
        message["From"] = from_addr
        message["To"] = ", ".join(to_addr)
        message["Subject"] = subject

        # Attach the CSV file
        with open(filename, "rb") as file:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {filename}")
        message.attach(part)

        # Attach the email body
        message.attach(MIMEText(body, "plain"))

        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(user=username, password=password)
            server.send_message(message)

        print("Email with attachment sent successfully.")

except HttpResponseError as err:
    print("Something fatal happened:")
    print(err)
