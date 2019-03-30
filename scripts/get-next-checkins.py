#!/usr/bin/env python

# This script outputs a list of the next scheduled checkins

import asyncio
import json

import boto3
import pendulum

SFN = boto3.client('stepfunctions')


def get_execution_history(execution_arn):
    e = SFN.get_execution_history(executionArn=execution_arn)
    state = json.loads(e['events'][-1]['stateEnteredEventDetails']['input'])
    return {'next': state['check_in_times']['next'], 'email': state['email']}


async def get_executions(args):
    # TODO(dw): pagination for > 100 executions
    executions = SFN.list_executions(
        stateMachineArn=args.state_machine_arn,
        statusFilter='RUNNING'
    )

    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(None, get_execution_history, e['executionArn'])
        for e in executions['executions']
    ]

    done, _ = await asyncio.wait(futures)
    results = [r.result() for r in done]
    sorted_results = sorted(results, key=lambda x: pendulum.parse(x['next']))

    if args.reverse:
        sorted_results = list(reversed(sorted_results))

    print(json.dumps(sorted_results[:args.count]))


def main(args):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_executions(args))
    loop.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-machine-arn', required=True)
    parser.add_argument('--count', type=int, required=False, default=5)
    parser.add_argument('--reverse', action='store_true')
    args = parser.parse_args()
    main(args)
