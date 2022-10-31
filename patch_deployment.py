import os
from kubernetes import config, client
import json


deployment_names = []
f = open("config", 'r')
file = f.read()

#print("Enter Deployemnt Name:")
#dep_name = input()

#print(dep_name)




config.load_kube_config(config_file='./config')

dep = client.api.AppsV1Api()

#t = open('./patch.json', 'r')
#txt = t.read()
#value = '{"spec": {"replicas": 3}}'
#print(txt)

print("Enter Deployment Name:")
d_name = input()

print("Enter Namespace:")

ns = input()

print(d_name, ns)

d = dep.list_deployment_for_all_namespaces()

#data = dep.list_namespaced_deployment(namespace=f'{ns}')
val = dep.read_namespaced_deployment(namespace=f'{ns}', name=f'{d_name}')

replica = val.spec.replicas

print(replica)


value = '{"spec": {"replicas": '+ f'{replica}' +'}}'
#txt = '{"spec": {"replicas": 1}}'
#print(txt)
print(value)


#for n in data.items:
    #print(n)
 #   print(n.spec.replicas)


modify = dep.patch_namespaced_deployment_scale(namespace=f'{ns}', name=f'{d_name}', body=json.loads(value))
print(modify)
