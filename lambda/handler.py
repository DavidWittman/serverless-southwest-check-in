#
# handler.py
# Lamba functions for interacting with the Southwest API
#

import json
import logging
import os
import re
import sys

import boto3

# Add vendored dependencies to path
sys.path.append('./vendor')

import pendulum     # NOQA
import swa          # NOQA

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# S3 bucket where emails received by SES are stored
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')


def schedule_check_in(event, context):
    """
    Looks up a reservation using the Southwest API and returns the available
    check-in times as a descending list.

    Returns:
      {'check_in_times': {'remaining': ['check_in2', 'check_in1']}}

    """

    # We already have the check-in times, just schedule the next one.
    if 'check_in_times' in event:
        event['check_in_times']['next'] = event['check_in_times']['remaining'].pop()
        return event

    # New check-in, fetch reservation
    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']

    event['check_in_times'] = {}

    log.info("Looking up reservation {} for {} {}".format(confirmation_number,
                                                          first_name, last_name))
    reservation = swa.get_reservation(first_name, last_name, confirmation_number)
    log.debug("Reservation: {}".format(reservation))

    event['check_in_times']['remaining'] = _get_check_in_times_from_reservation(reservation)

    # Call ourself now that we have some check-in times.
    return schedule_check_in(event, None)


def _get_check_in_time(departure_time):
    """
    Receives a departure time in RFC3339 format:

        2017-02-09T07:50:00.000-06:00

    And returns the check in time (24 hours prior) as a pendulum time object
    """
    return pendulum.parse(departure_time).subtract(days=1)


def _get_check_in_times_from_reservation(reservation):
    """
    Return a sorted and reversed list of check-in times for a reservation as
    RFC3339 timestamps.

    Times are sorted and reversed so that the soonest check-in time may be
    popped from the end of the list.
    """

    flights = reservation['itinerary']['originationDestinations']

    times = [
        _get_check_in_time(segment['departureDateTime']) for flight in flights
        for segment in flight['segments']
        if _get_check_in_time(segment['departureDateTime']) > now
    ]

    return map(str, reversed(sorted(times)))


class NotLastCheckIn(Exception):
    """
    This exception is raised in the check_in handler when additional
    check-ins remain. It is used to form a ghetto loop as described above.
    TODO(dw): Finish this description
    """
    pass


def check_in(event, context):
    """
    TODO(dw): Fix description
    Retrieves reservations which are ready to be checked in from DynamoDB and
    checks them in via the Southwest API
    """

    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']
    email = event.get('email')

    log.info("Checking in {} {} ({})".format(first_name, last_name,
                                             confirmation_number))

    try:
        resp = swa.check_in(first_name, last_name, confirmation_number)
        log.info("Checked in {} {}!".format(first_name, last_name))
        log.debug("Check-in response: {}".format(resp))
    except Exception as e:
        log.error("Error checking in: {}".format(e))
        raise

    if email:
        log.info("Emailing boarding pass to {}".format(email))
        try:
            swa.email_boarding_pass(
                first_name, last_name, confirmation_number, email
            )
        except Exception as e:
            log.error("Error emailing boarding pass: {}".format(e))

    # Raise exception to schedule the next check-in
    # This is caught by AWS Step and then schedule_check_in is called again
    if len(event['check_in_times']['remaining']) > 0:
        raise NotLastCheckIn()


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


def _find_name_and_confirmation_number(msg):
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

    return dict(first_name=fname, last_name=lname, confirmation_number=reservation)


def receive_email(event, context):
    sfn = boto3.client('stepfunctions')
    ses_notification = event['Records'][0]['ses']
    # ARN of the AWS Step State Machine to execute when an email
    # is successfully parsed and a new check-in should run.
    state_machine_arn = os.getenv('STATE_MACHINE_ARN')

    log.debug("State Machine ARN: {}".format(state_machine_arn))
    log.debug("SES Notification: {}".format(ses_notification))

    ses_msg = SesMailNotification(ses_notification['mail'])

    try:
        reservation = _find_name_and_confirmation_number(ses_msg)
        log.info("Found reservation: {}".format(reservation))
    except Exception as e:
        log.error("Error scraping email {}: {}".format(ses_msg.message_id, e))
        return

    execution = sfn.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(reservation)
    )

    log.debug("State machine started at: {}".format(execution['startDate']))
    log.debug("Execution ARN: {}".format(execution['executionArn']))

    # Remove the startDate from the return value because datetime objects don't
    # easily serialize to JSON.
    del(execution['startDate'])

    return execution
