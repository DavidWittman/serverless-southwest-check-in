#!/usr/bin/env python

# This script retrieves a detailed list of the currently running checkins

import argparse
import concurrent.futures
import datetime
import json
import sys

import boto3

SFN = boto3.client('stepfunctions')

def format_date_fields(obj):
    for key in obj:
        if isinstance(obj[key], datetime.datetime):
            obj[key] = obj[key].isoformat()
    return obj

def get_execution_details(execution_arn):
    e = SFN.describe_execution(executionArn=execution_arn)
    e = format_date_fields(e)
    del e['ResponseMetadata']
    return e

def main(args):
    results = []
    state_machine_arn = args.state_machine_arn

    # TODO(dw): pagination for > 100 executions
    executions = SFN.list_executions(
        stateMachineArn=state_machine_arn,
        statusFilter='RUNNING'
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for e in executions['executions']:
            future = executor.submit(get_execution_details, e['executionArn'])
            futures.append(future)
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
             
    print(json.dumps(results))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-machine-arn', required=True)
    args = parser.parse_args()
    main(args)
