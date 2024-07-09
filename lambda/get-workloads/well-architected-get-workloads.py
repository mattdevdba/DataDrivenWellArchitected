import boto3
import botocore
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#################
# Boto3 Clients #
#################
wa_client = boto3.client('wellarchitected')
event_client = boto3.client('events')

##############
# Parameters #
##############
# The maximum number of results the API can return in a list workloads call.
list_workloads_max_results_maximum = 50

def get_all_workloads():
    # Get a list of all workloads
    list_workloads_result = wa_client.list_workloads(MaxResults=list_workloads_max_results_maximum)
    logger.info(f'Found {len(list_workloads_result)} Well-Archtected workloads.')
    workloads_all = list_workloads_result['WorkloadSummaries']
    while 'NextToken' in list_workloads_result:
        next_token = list_workloads_result['NextToken']
        list_workloads_result = wa_client.list_workloads(
            MaxResults=list_workloads_max_results_maximum, NextToken=next_token
        )
        workloads_all += list_workloads_result['WorkloadSummaries']
    return (workloads_all)

def put_event(workload_id):

    detailjsonstring = {"workload_id":workload_id}

    response = event_client.put_events(
        Entries=[
            {
                'Source': 'get-workloads',
                'DetailType': 'well-architected-workload',
                'Detail': json.dumps(detailjsonstring),
                'EventBusName': 'cdl-well-architected-bus'
            }
        ]
    )

    print(response)

def lambda_handler(event, context):
    workloads_all = get_all_workloads()
    # Generate workload JSON file
    logger.info(f'Generate JSON object for each workload.')

    for workload in workloads_all:
        # Get workload info from WAR Tool API,
        workload_id = workload['WorkloadId']
        put_event(workload_id)
