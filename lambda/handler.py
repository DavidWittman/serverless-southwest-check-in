#
# lambda.py
# Lamba functions for interacting with the Southwest API
#

import logging
import os
import re
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

dynamo = boto3.client('dynamodb')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')


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
    Returns the future check-in times from a Southwest reservation response.

    Times are represented as a Unix timestamp, and any check-ins which are
    before the current time are ignored.
    """
    now = pendulum.now().int_timestamp
    flights = reservation['itinerary']['originationDestinations']

    return [
        _get_check_in_time(segment['departureDateTime']) for flight in flights
        for segment in flight['segments']
        if _get_check_in_time(segment['departureDateTime']) > now
    ]


def add(event, context):
    """
    Looks up a reservation and adds check in times to DynamoDB
    """

    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']
    # Optional parameters
    email = event.get('email')

    log.info("Looking up reservation {} for {} {}".format(confirmation_number,
                                                          first_name, last_name))
    reservation = swa.get_reservation(first_name, last_name, confirmation_number)
    log.debug("Reservation: {}".format(reservation))

    check_in_times = _get_check_in_times_from_reservation(reservation)

    for check_in_time in check_in_times:
        log.info("Scheduling check-in at {}".format(check_in_time))

        item = dict(
            check_in=check_in_time,
            reservation=confirmation_number,
            first_name=first_name,
            last_name=last_name
        )
        if email is not None:
            item['email'] = email

        log.debug("Adding check-in to Dynamo: {}".format(item))
        dynamo.put_item(Item=item)

    return "Successfully added {} check-in(s) for reservation {}: {}".format(
        len(check_in_times), confirmation_number, check_in_times)


def _delete_check_in(check_in_time, reservation):
    log.info("Removing completed check-in from DynamoDB")
    try:
        resp = dynamo.delete_item(Key={'check_in': check_in_time, 'reservation': reservation})
        if resp['HTTPStatusCode'] != 200:
            raise Exception("HTTP Error from DynamoDB: {}".format(resp))
    except Exception as e:
        log.error("Error deleting item from DynamoDB: {}".format(e))


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
            continue

        if 'email' in r:
            log.info("Emailing boarding pass to {}".format(r['email']))
            try:
                swa.email_boarding_pass(r['first_name'], r['last_name'], r['reservation'], r['email'])
            except Exception as e:
                log.error("Error emailing boarding pass: {}".format(e))

        _delete_check_in(this_minute, r['reservation'])


class ReservationNotFoundError(Exception):
    pass


class SesMailNotification(object):
    def __init__(self, data, s3_bucket=S3_BUCKET_NAME):
        self.data = data
        self.subject = data['commonHeaders']['subject']
        self.source = data['source']
        self.from_header = data['commonHeaders']['from']
        self.message_id = data['messageId']
        self._body = None
        # S3 bucket where SES messages are saved to
        self.s3_bucket = s3_bucket

    def body(self):
        """
        Retrieves the body of the email from S3.

        This requires that you set up a previous action in your SES rules to
        store the message in S3.
        """

        if self._body is None:
            log.debug("Downloading message body from s3://{}/{}".format(
                self.s3_bucket, self.message_id))
            s3 = boto3.client('s3')
            obj = s3.get_object(Bucket=self.s3_bucket, Key=self.message_id)
            self._body = obj['Body'].read().decode('utf-8')

        return self._body


def _find_name_and_reservation(msg):
    """
    Searches through the SES notification for passenger name
    and reservation number.
    """

    fname, lname, reservation = None, None, None

    # Try to match `(5PK4YZ) | 22APR17 | AUS-MCI | Wittman/David`
    match = re.search(r"\(([A-Z0-9]{6})\).*\| (\w+\/\w+)", msg.subject)

    if match:
        log.debug("Found a reservation email: {}".format(msg.subject))
        reservation = match.group(1)
        lname, fname = match.group(2).split('/')

    elif "Here's your itinerary!" in msg.subject:
        log.debug("Found an itinerary email: {}".format(msg.subject))

        match = re.search(r"\(([A-Z0-9]{6})\)", msg.subject)
        if match:
            reservation = match.group(1)

        log.debug("Reservation found: {}".format(reservation))

        regex = r"PASSENGER([\w\s]+)Check in"
        match = re.search(regex, msg.body())

        if match:
            # TODO(dw): This makes assumptions about the name,
            # specifically that the first word is their first name and the
            # last word is their last name.
            log.debug("Passenger matched. Parsing first and last name")
            name_parts = match.group(1).strip().split(' ')
            fname, lname = name_parts[0], name_parts[-1]

    log.info("Passenger: {} {}, Confirmation Number: {}".format(
        fname, lname, reservation))

    if not all([fname, lname, reservation]):
        raise ReservationNotFoundError("Unable to find reservation in email id {}".format(
            msg.message_id))

    return fname, lname, reservation


def receive_email(event, context):
    ses_notification = event['Records'][0]['ses']
    log.debug("SES Notification: {}".format(ses_notification))

    ses_msg = SesMailNotification(ses_notification['mail'])

    try:
        fname, lname, reservation = _find_name_and_reservation(ses_msg)
        log.info("Found reservation {} for {} {}".format(reservation, fname, lname))
    except Exception as e:
        log.error("Error scraping email {}: {}".format(ses_msg.message_id, e))
        return 1
