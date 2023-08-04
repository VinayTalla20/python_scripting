import subprocess
import os
import kubernetes
import kopf
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

# To get Values from pod Environments variables
REQUIRED_MAILS = os.getenv("REQUIRED_MAILS")
CLUSTER_ENV = os.getenv("CLUSTER_ENV")

SEND_MAILS = []

#
mail = REQUIRED_MAILS.split(",")
print("print type", type(mail), "printing mail data", mail)

for to_mails in mail:
    SEND_MAILS.append(to_mails)

# creating ApiConnection to Cluster using Kubernetes Config file
APi_Connection = kubernetes.config.load_kube_config(config_file="/home/vinay/.kube/config")

print("current context", kubernetes.config.list_kube_config_contexts()[1]["name"])


# handler to watch any creation of JObs
@kopf.on.create('batch', 'v1', 'jobs')
def watch_jobs(spec, **kwargs):
    resource_name = kwargs["body"]["metadata"]["name"]
    job_namespace = kwargs["body"]["metadata"]["namespace"]
    print("JOB NAME:", resource_name, " in Namespace:", job_namespace)

    job_status_api = kubernetes.client.BatchV1Api().read_namespaced_job(namespace=job_namespace, name=resource_name)

    while True:
        job_status = job_status_api.status.conditions[0].type
        job_status_message = job_status_api.status.conditions[0].message

        if job_status == "Failed":
            print("JOb Message", job_status_message)
            job_name = job_status_api.metadata.name
            print("JOB NAME", job_name)

            break

    print(f"The Status of job name {job_name} has the status of {job_status} in the namespace {job_namespace}")
    print("JOb Message", job_status_message)
    job_status_job_name = kubernetes.client.BatchV1Api().read_namespaced_job(namespace=job_namespace, name=job_name)
    print("Status of failed jobs", job_status_job_name.status.conditions[0].last_transition_time)
    time_required_utc = job_status_job_name.metadata.creation_timestamp

    time_required_utc = str(time_required_utc)  # 2023-08-02 07:40:17+00:00
    print("Time at Job creation in utc  ", time_required_utc)
    time_required_utc = time_required_utc.split("+")[0]  # 2023-08-02 07:40:17

    before_time = time_required_utc.split(' ')[1]  # 07:40:17
    print("Only time", before_time)
    before_time_hour = before_time.split(":")[0]  # 07
    before_time_minute = before_time.split(":")[1]  # 40

    if before_time_minute.startswith("0"):
        after_time_minute = int(before_time_minute) + 1
        to_concatenate = "0"
        after_time_minute = to_concatenate + str(after_time_minute)
    else:
        print("ok, adding one minute")
        after_time_minute = int(before_time_minute) + 1

    complete_before_time = before_time_hour + ":" + before_time_minute  # 07:40

    complete_after_time = before_time_hour + ":" + str(after_time_minute)

    print("before time:", complete_before_time)
    print("After Time:", complete_after_time)

    # converting UTC to IST time
    time_required_converted_str_ist = datetime.strptime(time_required_utc, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=330)
    print("Time of creation of job", time_required_utc)

    time_present = str(datetime.now()).split(".")[0]

    time_present_str = datetime.strptime(time_present, '%Y-%m-%d %H:%M:%S')
    time_required_to_get_logs = time_present_str - time_required_converted_str_ist

    # convert to minutes
    time_required_to_get_logs = timedelta.total_seconds(time_required_to_get_logs) / 60 + 1

    file_name = f"{job_name}-logs.txt"
    # kubectl logs command to get logs from cluster from specific timestamp
    # kubectl logs -n kube-system italentstg-ingress-nginx-controller-5784b465fb-7bpkw --since-time '2023-08-02T05:20:20Z' --timestamps=true --prefix
    print(os.system(
        f"kubectl logs -n default -l app=logger --since {time_required_to_get_logs}m  --timestamps=true --prefix --tail 2 | grep -i 'logger' >> {file_name}"))

    # SMTP connections
    smtp_server = ""
    smtp_port = 
    username = ""
    password = ""
    from_addr = ""
    to_addr = SEND_MAILS
    subject = f"SmartConX Dev {job_name} Job has Failed"

    body = "Hi Team,\n Please find the attached logs for further analysis.\n"

    with open(file_name, "r") as content_file:
        job_message = content_file.readlines()
        print("Log Content", job_message)
        body += str(job_message)
        content_file.close()


    body += "\n\nThanks,\nDevOps Team"

    # Create a multipart message
    message = MIMEMultipart()
    message["From"] = from_addr
    message["To"] = ", ".join(to_addr)
    message["Subject"] = subject

    with open(file_name, "rb") as file:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(file.read())

        # Attach the email body
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename= {file_name}")
        message.attach(part)

    message.attach(MIMEText(body, "plain"))

    # Send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(user=username, password=password)
        server.send_message(message)
        print("Email with attachment sent successfully.")
