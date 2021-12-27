import json

import boto3


def get_headers():
    ssm = boto3.client('ssm')
    result = ssm.get_parameter(Name='/southwest/headers')
    return json.loads(result['Parameter']['Value'])
