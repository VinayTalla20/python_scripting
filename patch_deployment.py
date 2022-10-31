import os
from kubernetes import config, client
import json


deployment_names = []
f = open("config", 'r')
file = f.read()


config.load_kube_config(config_file='./config')

dep = client.api.AppsV1Api()

t = open('./patch.json', 'r')
txt = t.read()
value = '{"spec": {"replicas": 2}}'
print(txt)

d = dep.list_deployment_for_all_namespaces()
modify = dep.patch_namespaced_deployment_scale(namespace='default', name='nginx', body=json.loads(value))
print(modify)

print('-' *35)

for x in d.items:

    deploy_name = x.metadata.name
    deployment_names.append(deploy_name)

print(deployment_names)

if 'nginx' in deployment_names:
    print("success")
