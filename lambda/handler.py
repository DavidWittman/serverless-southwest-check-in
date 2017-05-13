#
# handler.py
# Lamba functions for scheduling check-ins via the Southwest API
#

import json
import logging
import os
import sys
import uuid

import boto3

# Add vendored dependencies to path
sys.path.append('./vendor')

from lib import swa, email, exceptions  # NOQA

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def schedule_check_in(event, context):
    """
    This function serves two purposes:

        1) For new executions, it looks up the reservation via the Southwest
           API and returns the check-in times (described below).

        2) In the event there are multiple check-ins, this function is called
           again by the AWS Step state machine to schedule the next available
           check-in time. It does this by popping a value from
           `check_in_times.remaining` into `check_in_times.next`.

    Returns a dictionary of the next and remaining check-in times in RFC 3339
    format. Ex:

        {
            "check_in_times": {
                "next": "2017-05-06T20:40:00-04:00",
                "remaining": [
                    "2017-05-12T20:40:00-04:00",
                    "2017-05-09T20:40:00-04:00"
                ]
            }
        }

    """

    # We already have the check-in times, just schedule the next one.
    if 'check_in_times' in event:
        event['check_in_times']['next'] = \
            event['check_in_times']['remaining'].pop()
        return event

    # New check-in, fetch reservation
    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']
    email = event['email']

    log.info("Looking up reservation {} for {} {}".format(confirmation_number,
                                                          first_name, last_name))
    reservation = swa.Reservation.from_passenger_info(
        first_name, last_name, confirmation_number
    )
    log.debug("Reservation: {}".format(reservation))

    result = {
        'check_in_times': {
            'remaining': reservation.check_in_times,
        },
        'passengers': reservation.passengers,
        'confirmation_number': confirmation_number,
        'email': email
    }

    # Call ourself now that we have some check-in times.
    return schedule_check_in(result, None)


def check_in(event, context):
    """
    This function is triggered at check-in time and completes the check-in via
    the Southwest API and emails the reservation, if requested.
    """

    confirmation_number = event['confirmation_number']
    email = event['email']

    # Support older check-ins which did not support multiple passengers
    if 'passengers' not in event:
        event['passengers'] = [
            (event['first_name'], event['last_name'])
        ]

    # TODO(dw): This can be done with one API call by passing multiple
    # names with the checkin call in the form:
    # names: [{'firstName': "George", 'lastName': "Bush"}]
    for first_name, last_name in event['passengers']:
        log.info("Checking in {} {} ({})".format(
            first_name, last_name, confirmation_number
        ))

        try:
            resp = swa.check_in(first_name, last_name, confirmation_number)
            log.info("Checked in {} {}!".format(first_name, last_name))
            log.debug("Check-in response: {}".format(resp))
        except Exception as e:
            log.error("Error checking in: {}".format(e))
            raise

        # TODO(dw): Same as above, this supports passing multiple names
        # to the Southwest API call.
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
        raise exceptions.NotLastCheckIn()


def _get_sfn_execution_name(reservation):
    """
    Generate a human-readable execution named composed of the passenger's
    first and last name follwed by a UUID
    """
    name = "{}-{}-{}".format(
        reservation['last_name'].lower(),
        reservation['first_name'].lower(),
        uuid.uuid4()
    )
    return name


def receive_email(event, context):
    """
    This function is triggered when as an SES Action when a new e-mail is
    received. It scrapes the email to find the name and confirmation
    number of the passenger to check-in, and then executes the AWS Step
    state machine provided in the `STATE_MACHINE_ARN` environment variable.
    """

    sfn = boto3.client('stepfunctions')
    ses_notification = event['Records'][0]['ses']
    # ARN of the AWS Step State Machine to execute when an email
    # is successfully parsed and a new check-in should run.
    state_machine_arn = os.getenv('STATE_MACHINE_ARN')

    log.debug("State Machine ARN: {}".format(state_machine_arn))
    log.debug("SES Notification: {}".format(ses_notification))

    ses_msg = email.SesMailNotification(ses_notification['mail'])

    try:
        reservation = email.find_name_and_confirmation_number(ses_msg)
        log.info("Found reservation: {}".format(reservation))
    except Exception as e:
        log.error("Error scraping email {}: {}".format(ses_msg.message_id, e))
        return

    # Don't add the email if it's straight from southwest.com
    if not ses_msg.source.endswith('southwest.com'):
        reservation['email'] = ses_msg.source

    execution = sfn.start_execution(
        stateMachineArn=state_machine_arn,
        name=_get_sfn_execution_name(reservation),
        input=json.dumps(reservation)
    )

    log.debug("State machine started at: {}".format(execution['startDate']))
    log.debug("Execution ARN: {}".format(execution['executionArn']))

    # Remove the startDate from the return value because datetime objects don't
    # easily serialize to JSON.
    del(execution['startDate'])

    return execution
