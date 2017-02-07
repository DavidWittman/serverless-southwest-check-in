#
# lambda.py
# Lamba functions for interacting with the Southwest API
#

import logging
import os
import sys

import boto3

from boto3.dynamodb.conditions import Key

# Add vendored dependencies to path
sys.path.append('./vendor')

import pendulum     # NOQA
import swa          # NOQA

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

DYNAMO_TABLE_NAME = os.getenv('DYNAMO_TABLE_NAME')
dynamo = boto3.resource('dynamodb').Table(DYNAMO_TABLE_NAME)


def _get_minute_timestamp(dt):
    """
    Return a timestamp of the most recent minute from a Pendulum datetime object

    >>> now = pendulum.now()
    >>> print(now)
    2017-02-06T22:14:09.222312-06:00
    >>> _get_minute_timestamp(now)
    1486440840
    """
    return dt.replace(second=0, microsecond=0).int_timestamp


def _get_check_in_time(departure_time):
    """
    Receives a departure time in RFC3339 format:

        2017-02-09T07:50:00.000-06:00

    And returns the check in time (24 hours prior) as a unix timestamp
    """
    check_in_time = pendulum.parse(departure_time).subtract(days=1)
    return _get_minute_timestamp(check_in_time)


def _get_check_in_times_from_reservation(reservation):
    """
    """
    flights = reservation['itinerary']['originationDestinations']
    return [
        _get_check_in_time(segment['departureDateTime']) for flight in flights
        for segment in flight['segments']
    ]


def add(event, context):
    """
    Looks up a reservation and adds check in times to DynamoDB
    """
    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']

    log.info("Looking up reservation {} for {} {}".format(confirmation_number,
                                                          first_name, last_name))
    reservation = swa.get_reservation(first_name, last_name, confirmation_number)
    log.debug("Reservation: {}".format(reservation))

    check_in_times = _get_check_in_times_from_reservation(reservation)
    log.info("Scheduling check-ins at {}".format(check_in_times))

    for c in check_in_times:
        item = dict(
            check_in=c,
            reservation=confirmation_number,
            first_name=first_name,
            last_name=last_name,
            status='pending'
        )

        log.debug("Adding check-in to Dynamo: {}".format(item))
        dynamo.put_item(Item=item)

    # TODO(dw): Better output. What times are we going to check in?
    return "Successfully added {} check-ins for reservation {}".format(len(check_in_times), confirmation_number)


def check_in(event, context):
    """
    Retrieves reservations which are ready to be checked in from DynamoDB and
    checks them in via the Southwest API
    """

    # Get a timestamp for the current minute
    this_minute = _get_minute_timestamp(pendulum.now())
    log.debug("Current minute: {}".format(this_minute))

    response = dynamo.query(KeyConditionExpression=Key('check_in').eq(this_minute))
    log.debug("Response: {}".format(response))
    log.info("Found {} reservation(s) to check in".format(response['Count']))

    # Check in!
    for r in response['Items']:
        log.info("Checking in {first_name} {last_name} ({reservation})".format(**r))
        try:
            resp = swa.check_in(r['first_name'], r['last_name'], r['reservation'])
            log.info("Checked in {first_name} {last_name}!".format(**r))
            log.debug("Check-in response: {}".format(resp))
        except Exception as e:
            log.error("Error checking in: {}".format(e))
