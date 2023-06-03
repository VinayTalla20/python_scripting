import json
import yaml
from kubernetes import config
import kubernetes
from datetime import datetime

config.load_kube_config(config_file="")


namespace = "default"
pod_name = []
print(namespace)
pod_api = kubernetes.client.CoreV1Api()

pod_list = pod_api.list_namespaced_pod(namespace=namespace)
mq_pod_list = pod_api.list_namespaced_pod(namespace=namespace)
print(mq_pod_list.items[0].status.container_statuses[0].state.running.started_at)


for i in pod_list.items:
    pod = i.metadata.name
    pod_name.append(pod)

print(pod_name)


for mq_pod in pod_name:
    get_label = pod_api.read_namespaced_pod(namespace=namespace, name=mq_pod)
    if get_label.metadata.labels["app"] == "active-mq":
        print("found mq")
        print("pod name is:",mq_pod)
        mq_get_time_api = pod_api.read_namespaced_pod(namespace=namespace, name=mq_pod)
        print("MQ time ",mq_get_time_api.status.container_statuses[0].state.running.started_at)
        mq_get_time = str(mq_get_time_api.status.container_statuses[0].state.running.started_at)
        mq_pod_name = mq_pod


for each_pod in pod_name:
    if each_pod != mq_pod_name:
        print("not mq pod:",each_pod)
        each_pod_results = pod_api.read_namespaced_pod(namespace=namespace, name=each_pod)
        print(f"pod name is: {each_pod}, and its timestamp is: ", each_pod_results.status.container_statuses[0].state.running.started_at)
        if mq_get_time > str(each_pod_results.status.container_statuses[0].state.running.started_at):
            print(f"The pod {each_pod} is running before the Active-MQ so deleting this pod")
            #pod_api.delete_namespaced_pod(namespace=namespace, name=each_pod)
            print(f"This {each_pod} has deleted")



print("MQ time",mq_get_time)
