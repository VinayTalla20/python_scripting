import os
import re
import smtplib
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(tenant_id="",
                                    client_id="",
                                    client_secret="")

client = LogsQueryClient(credential)

required_nodeNames = []
required_podNames = []
Memory_WorkingSet_Max_Values = []
Memory_WorkingSet_Min_Values = []
pod_cpu_max_values = []
pod_cpu_min_values = []
Memory_RSS_Max_Values = []
Memory_RSS_Min_Values = []
node_RSS_memory_max_values = []
node_RSS_memory_min_values = []
node_memory_workingset_min_values = []
node_memory_workingset_max_values = []
node_memory_limit_values = []
node_cpu_metric_Max_values = []
node_cpu_metric_Min_values = []
node_cpu_limit_values = []

pod_filename = "pod_mem_metrics.csv"
node_filename = "node_mem_metrics.csv"
# required_date = | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))

def pod_memory_workingSet():
    Metrics_MemoryWorkingSet_Pods_Query = """
            
            KubePodInventory
            | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
            | where ClusterName == "italent-ics-prod-aks"
            | where Namespace == "syndication"
            | summarize arg_max(TimeGenerated, *) by ContainerName
            | project Name, ContainerName
            | join kind = inner (
                Perf
                | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
                | where ObjectName == 'K8SContainer'
                | where CounterName == 'memoryWorkingSetBytes'    
                | where InstanceName contains 'italent-ics-prod-aks'
                | extend ContainerNameParts = split(InstanceName, '/')
                | extend ContainerNamePartCount = array_length(ContainerNameParts)            
                | extend PodUIDIndex = ContainerNamePartCount - 2, ContainerNameIndex = ContainerNamePartCount - 1 
                | extend ContainerName = strcat(ContainerNameParts[PodUIDIndex], '/', ContainerNameParts[ContainerNameIndex])
                | project TimeGenerated, ContainerName, CounterValue
            ) on ContainerName
            | order by TimeGenerated asc
            | project TimeGenerated, Name, CounterValue=(CounterValue)
            """

    try:
        response = client.query_workspace(
            workspace_id="93227332-2bac-402f-b059-f2eb68b6a06a",
            query=Metrics_MemoryWorkingSet_Pods_Query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            pod_mem_metrics = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            podNames = pod_mem_metrics["Name"].values
            # deDuplicating pod Names
            for podname in podNames:
                if podname not in required_podNames:
                    required_podNames.append(podname)
            print("After DeDuplicating ", required_podNames, "array length", len(required_podNames))

            for query_pod in required_podNames:
                specific_pod_metrics = pod_mem_metrics.loc[(pod_mem_metrics["Name"] == f"{query_pod}")]
                pod_mem_value = specific_pod_metrics["CounterValue"]
                required_array = np.array(pod_mem_value.values)

                Memory_WorkingSet_Max = np.max(required_array)

                time_max_value = pod_mem_metrics.loc[(pod_mem_metrics["CounterValue"] == Memory_WorkingSet_Max)]

                max_required_time = str(time_max_value["TimeGenerated"].values[0])
                max_required_time = max_required_time.split('.')[0]

                Memory_WorkingSet_Max = np.max(required_array) / 1048576
                Memory_WorkingSet_Max = str(round(Memory_WorkingSet_Max, 2))

                Memory_WorkingSet_Max += f" MB    {max_required_time}"

                Memory_WorkingSet_Max_Values.append(Memory_WorkingSet_Max)

                Memory_WorkingSet_Min = np.min(required_array)
                time_min_value = pod_mem_metrics.loc[(pod_mem_metrics["CounterValue"] == Memory_WorkingSet_Min)]

                min_required_time = str(time_min_value["TimeGenerated"].values[0])
                min_required_time = min_required_time.split('.')[0]

                Memory_WorkingSet_Min = np.min(required_array) / 1048576
                Memory_WorkingSet_Min = str(round(Memory_WorkingSet_Min, 2))
                Memory_WorkingSet_Min += f" MB    {min_required_time}"
                Memory_WorkingSet_Min_Values.append(Memory_WorkingSet_Min)


    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


def pod_memory_RSS():
    Metrics_MemoryRSS_Pods_Query = """

            KubePodInventory
        | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
        | where ClusterName == "italent-ics-prod-aks"
        | where Namespace == "syndication"
        | summarize arg_max(TimeGenerated, *) by ContainerName
        | project Name, ContainerName
        | join kind = inner (
            Perf
            | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
            | where ObjectName == 'K8SContainer'
            | where CounterName == 'memoryRssBytes'    
            | where InstanceName contains 'italent-ics-prod-aks'
            | extend ContainerNameParts = split(InstanceName, '/')
            | extend ContainerNamePartCount = array_length(ContainerNameParts)            
            | extend PodUIDIndex = ContainerNamePartCount - 2, ContainerNameIndex = ContainerNamePartCount - 1 
            | extend ContainerName = strcat(ContainerNameParts[PodUIDIndex], '/', ContainerNameParts[ContainerNameIndex])
            | project TimeGenerated, ContainerName, CounterValue
        ) on ContainerName
        | order by TimeGenerated asc
        | project TimeGenerated, Name, CounterValue=(CounterValue)
            """

    try:
        response = client.query_workspace(
            workspace_id="93227332-2bac-402f-b059-f2eb68b6a06a",
            query=Metrics_MemoryRSS_Pods_Query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            pod_mem_metrics = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            for query_pod in required_podNames:
                # print("Pod Name", query_pod)
                specific_pod_metrics = pod_mem_metrics.loc[(pod_mem_metrics["Name"] == f"{query_pod}")]
                pod_mem_value = specific_pod_metrics["CounterValue"]
                required_array = np.array(pod_mem_value.values)

                Memory_RSS_Max = np.max(required_array)
                # print("Required  Max Value", Memory_WorkingSet_Max)
                #
                time_max_value = pod_mem_metrics.loc[(pod_mem_metrics["CounterValue"] == Memory_RSS_Max)]
                # print(time_max_value)
                max_required_time = str(time_max_value["TimeGenerated"].values[0])
                max_required_time = max_required_time.split('.')[0]

                Memory_RSS_Max = np.max(required_array) / 1048576
                Memory_RSS_Max = str(round(Memory_RSS_Max, 2))

                Memory_RSS_Max += f" MB    {max_required_time}"
                Memory_RSS_Max_Values.append(Memory_RSS_Max)

                Memory_RSS_Min = np.min(required_array)
                time_min_value = pod_mem_metrics.loc[(pod_mem_metrics["CounterValue"] == Memory_RSS_Min)]

                min_required_time = str(time_min_value["TimeGenerated"].values[0])
                min_required_time = min_required_time.split('.')[0]

                Memory_RSS_Min = np.min(required_array) / 1048576
                Memory_RSS_Min = str(round(Memory_RSS_Min, 2))
                Memory_RSS_Min += f" MB    {min_required_time}"
                Memory_RSS_Min_Values.append(Memory_RSS_Min)


    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


def pod_cpu_metrics():
    pod_cpu_metrics_query = """
    KubePodInventory
    | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
    | where ClusterName == "italent-ics-prod-aks"
    | where Namespace == "syndication"
    | summarize arg_max(TimeGenerated, *) by ContainerName
    | project Name, ContainerName
    | join kind = inner (
        Perf
        | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
        | where ObjectName == 'K8SContainer'
        | where CounterName == 'cpuUsageNanoCores'
        | where InstanceName contains 'italent-ics-prod-aks'
        | extend ContainerNameParts = split(InstanceName, '/')
        | extend ContainerNamePartCount = array_length(ContainerNameParts)            
        | extend PodUIDIndex = ContainerNamePartCount - 2, ContainerNameIndex = ContainerNamePartCount - 1 
        | extend ContainerName = strcat(ContainerNameParts[PodUIDIndex], '/', ContainerNameParts[ContainerNameIndex])
        | project TimeGenerated, ContainerName, CounterValue
    ) on ContainerName
    | order by TimeGenerated asc
    | project TimeGenerated, Name, CounterValue=(CounterValue / 1000000)
    """

    try:
        response = client.query_workspace(
            workspace_id="93227332-2bac-402f-b059-f2eb68b6a06a",
            query=pod_cpu_metrics_query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            pod_cpu_metrics = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            for cpu_pod in required_podNames:
                specific_cpu_metrics = pod_cpu_metrics.loc[(pod_cpu_metrics["Name"] == f"{cpu_pod}")]
                pod_cpu_value = specific_cpu_metrics["CounterValue"]
                required_array = np.array(pod_cpu_value.values)

                pod_cpu_max_value = np.max(required_array)
                pod_cpu_max_value = str(round(pod_cpu_max_value, 2))
                pod_cpu_max_values.append(pod_cpu_max_value)

                pod_cpu_min_value = np.min(required_array)
                pod_cpu_min_value = str(round(pod_cpu_min_value, 2))
                pod_cpu_min_values.append(pod_cpu_min_value)


    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


def podmetrics_createtable():
    pod_memory_workingSet()
    pod_memory_RSS()
    pod_cpu_metrics()
    pod_metrics_data = {
        'podNames': required_podNames,
        'Memory WorkingSet MinValues': Memory_WorkingSet_Min_Values,
        'Memory WorkingSet MaxValues': Memory_WorkingSet_Max_Values,
        'Memory RSS MaxValues': Memory_RSS_Min_Values,
        'Memory RSS MinValues': Memory_RSS_Max_Values,
        'CPU Min Values(Milli Cores)': pod_cpu_min_values,
        'CPU Max Values(Milli Cores)': pod_cpu_max_values

    }

    pod_table = pd.DataFrame(pod_metrics_data)
    print(pod_table)
    pod_table.to_csv(pod_filename, mode='a', index=False)

podmetrics_createtable()

def node_memory_RSS():
    node_memory_RSS_Query = """
    Perf
    | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
    | where ObjectName == "K8SNode"
    | where CounterName == "memoryRssBytes"
    | where InstanceName contains 'italent-ics-prod-aks'
    | order by TimeGenerated asc
    | project TimeGenerated, Node=Computer, MemoryWorkingSet=(CounterValue)
    """

    try:
        response = client.query_workspace(
            workspace_id="93227332-2bac-402f-b059-f2eb68b6a06a",
            query=node_memory_RSS_Query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            node_memory_RSS_metrics = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            Node_array = node_memory_RSS_metrics["Node"].values
            # DeDuplicating Arrays

            for nodeName in Node_array:
                if nodeName not in required_nodeNames:
                    required_nodeNames.append(nodeName)
            print("After DeDuplicating ", required_nodeNames, "array length", len(required_nodeNames))

            for query_node in required_nodeNames:
                specific_node_metrics = node_memory_RSS_metrics.loc[
                    (node_memory_RSS_metrics["Node"] == f"{query_node}")]
                node_RSS_memory_value = specific_node_metrics["MemoryWorkingSet"]
                required_array = np.array(node_RSS_memory_value.values)

                node_RSS_memory_max_value = np.max(required_array)
                node_RSS_memory_max_value = node_RSS_memory_max_value / 1073741824
                node_RSS_memory_max_value = str(round(node_RSS_memory_max_value, 2))
                node_RSS_memory_max_value += " GB"

                node_RSS_memory_min_value = np.min(required_array)
                node_RSS_memory_min_value = node_RSS_memory_min_value / 1073741824
                node_RSS_memory_min_value = str(round(node_RSS_memory_min_value, 2))
                node_RSS_memory_min_value += " GB"

                node_RSS_memory_max_values.append(node_RSS_memory_max_value)

                node_RSS_memory_min_values.append(node_RSS_memory_min_value)



    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


def node_memory_WorkingSet():
    node_memory_WorkingSet_Query = """
    Perf
    | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
    | where ObjectName == "K8SNode"
    | where CounterName == "memoryWorkingSetBytes"
    | where InstanceName contains 'italent-ics-prod-aks'
    | order by TimeGenerated asc
    | project TimeGenerated, Node=Computer, MemoryWorkingSet=(CounterValue)
     """

    try:
        response = client.query_workspace(
            workspace_id="93227332-2bac-402f-b059-f2eb68b6a06a",
            query=node_memory_WorkingSet_Query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            node_memory_WorkingSet_metrics = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            # print(node_memory_WorkingSet_metrics.values)

            for query_node in required_nodeNames:
                specific_node_metrics = node_memory_WorkingSet_metrics.loc[
                    (node_memory_WorkingSet_metrics["Node"] == f"{query_node}")]
                node_memory_workingset_value = specific_node_metrics["MemoryWorkingSet"]
                required_array = np.array(node_memory_workingset_value.values)
                # print(required_array)

                node_memory_workingset_max_value = np.max(required_array)
                node_memory_workingset_max_value = node_memory_workingset_max_value / 1073741824
                node_memory_workingset_max_value = str(round(node_memory_workingset_max_value, 2))
                node_memory_workingset_max_value += " GB"
                node_memory_workingset_max_values.append(node_memory_workingset_max_value)

                node_memory_workingset_min_value = np.min(required_array)
                node_memory_workingset_min_value = node_memory_workingset_min_value / 1073741824
                node_memory_workingset_min_value = str(round(node_memory_workingset_min_value, 2))
                node_memory_workingset_min_value += " GB"
                node_memory_workingset_min_values.append(node_memory_workingset_min_value)


    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


def node_memory_limit():
    node_memory_limit_query = """
    Perf
    | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
    | where ObjectName == "K8SNode"
    | where CounterName == "memoryCapacityBytes"
    | where InstanceName contains 'italent-ics-prod-aks'
    | summarize arg_max(TimeGenerated, *) by Computer
    | project Node=Computer, Memory=(CounterValue)
    """

    try:
        response = client.query_workspace(
            workspace_id="93227332-2bac-402f-b059-f2eb68b6a06a",
            query=node_memory_limit_query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            node_memory_limit_metrics = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            for query_node in required_nodeNames:
                specific_node_memory_metrics = node_memory_limit_metrics.loc[
                    (node_memory_limit_metrics["Node"] == f"{query_node}")]
                node_memory_limit_value = specific_node_memory_metrics["Memory"]

                node_memory_limit_value = node_memory_limit_value.values
                for node_limit in node_memory_limit_value:
                    node_memory_limit_value = node_limit / 1073741824
                    node_memory_limit_value = str(round(node_memory_limit_value, 2))
                    node_memory_limit_value += " GB"

                    node_memory_limit_values.append(node_memory_limit_value)






    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


def node_cpu_metrics():
    node_cpu_metrics_query = """
         Perf
        | where ObjectName == "K8SNode"
        | where CounterName == "cpuUsageNanoCores"
        | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
        | where InstanceName contains 'italent-ics-prod-aks'
        | order by TimeGenerated asc
        | project TimeGenerated, Node=Computer, CPU=(CounterValue / 1000000)
         """

    try:
        response = client.query_workspace(
            workspace_id="93227332-2bac-402f-b059-f2eb68b6a06a",
            query=node_cpu_metrics_query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            node_cpu_metrics = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)

            # print(node_cpu_metrics)
            for query_node in required_nodeNames:
                specific_node_cpu_metrics = node_cpu_metrics.loc[(node_cpu_metrics["Node"] == f"{query_node}")]
                node_cpu_metric_value = specific_node_cpu_metrics["CPU"]

                required_array = np.array(node_cpu_metric_value.values)

                node_cpu_metric_Min_value = np.min(required_array)
                node_cpu_metric_Min_value = str(round(node_cpu_metric_Min_value, 2))
                node_cpu_metric_Min_values.append(node_cpu_metric_Min_value)

                node_cpu_metric_Max_value = np.max(required_array)
                node_cpu_metric_Max_value = str(round(node_cpu_metric_Max_value, 2))
                node_cpu_metric_Max_values.append(node_cpu_metric_Max_value)

    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


def node_cpu_limit():
    node_cpu_limit_query = """
    Perf
    | where TimeGenerated between (datetime('2023-06-18 05:00:00') .. datetime('2023-06-19 05:00:00'))
    | where ObjectName == "K8SNode"
    | where CounterName == "cpuCapacityNanoCores"
    | where InstanceName contains 'italent-ics-prod-aks'
    | summarize arg_max(TimeGenerated, *) by Computer
    | project Node=Computer, CPU=(CounterValue / 1000000000)
    """

    try:
        response = client.query_workspace(
            workspace_id="93227332-2bac-402f-b059-f2eb68b6a06a",
            query=node_cpu_limit_query,
            timespan=None

        )
        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            print(error)
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables
        for table in data:
            node_cpu_Limit_metrics = pd.DataFrame(data=table.rows, columns=table.columns)
            # Set display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", None)
            pd.set_option("display.max_colwidth", None)


            for query_node in required_nodeNames:
                specific_node_cpu_limti_metrics = node_cpu_Limit_metrics.loc[
                    (node_cpu_Limit_metrics["Node"] == f"{query_node}")]
                node_limit_value = specific_node_cpu_limti_metrics["CPU"]
                node_limit_value = node_limit_value.values
                for node_limit in node_limit_value:

                    node_cpu_limit_values.append(node_limit)



    except HttpResponseError as err:
        print("Something fatal happened:")
        print(err)


def node_metrics_createtable():
    node_memory_RSS()
    node_memory_WorkingSet()
    node_memory_limit()
    node_cpu_metrics()
    node_cpu_limit()

    node_metrics_data = {
        'NodeNames': required_nodeNames,
        'Node RSS Memory Min Values': node_RSS_memory_min_values,
        'Node RSS Memory Max Values': node_RSS_memory_max_values,
        'Node WorkingSet Min Values': node_memory_workingset_min_values,
        'Node WorkingSet Max Values': node_memory_workingset_max_values,
        'Node Memory Limit': node_memory_limit_values,
        'Node CPU Min Value(Milli Cores)': node_cpu_metric_Min_values,
        'Node CPU Max Value(Milli Cores)': node_cpu_metric_Max_values,
        'Node CPU Limit': node_cpu_limit_values

    }

    node_table = pd.DataFrame(node_metrics_data)
    print(node_table)
    node_table.to_csv(node_filename, mode='a', index=False)


node_metrics_createtable()
