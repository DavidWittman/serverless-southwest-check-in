#
# lambda.py
# Lamba functions for interacting with the Southwest API
#

import datetime
import os
import sys
import time

import boto3

from boto3.dynamodb.conditions import Key

import swa

# Add vendored dependencies to path. These are used in swa.py.
sys.path.append('./vendor')

DYNAMO_TABLE_NAME = os.getenv('DYNAMO_TABLE_NAME')
dynamo = boto3.resource('dynamodb').Table(DYNAMO_TABLE_NAME)


def _get_minute_timestamp(dt):
    """
    Returns the minute of a datetime object in unix timestamp form.

    In this example, the real time is 20:24:23 UTC, but it will be
    rounded down to the nearest minute and converted to an int
    >>> _get_timestamp()
    1486239840
    """
    minute = dt.replace(second=0, microsecond=0)
    return int(time.mktime(minute.timetuple()))


def add(event, context):
    """
    Looks up a reservation and adds check in times to DynamoDB
    """
    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']

    itinerary = swa.get_itinerary(first_name, last_name, confirmation_number)
    # TODO(dw): Fetch departure times from itinerary, convert to dt object,
    # round to nearest minute, subtract 24 hours, then add to DynamoDB


def check_in(event, context):
    """
    Retrieves reservations which are ready to be checked in from DynamoDB and
    checks them in via the Southwest API
    """

    # Get a timestamp for the current minute
    now = _get_minute_timestamp(datetime.datetime.now())
    response = dynamo.query(KeyConditionExpression=Key('check_in').eq(now))

    for reservation in response['Items']:
        # Check in!
