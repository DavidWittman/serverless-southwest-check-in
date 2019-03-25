import json
import logging
import os
import uuid

import boto3

import mail

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def _get_sfn_execution_name(reservation):
    """
    Generate a human-readable execution named composed of the passenger's
    first and last name follwed by a UUID
    """
    name = "{}-{}-{}".format(
        reservation['last_name'].lower().replace(' ', '-'),
        reservation['first_name'].lower(),
        uuid.uuid4()
    )
    return name


def main(event, context):
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

    ses_msg = mail.SesMailNotification(ses_notification['mail'])

    try:
        reservation = mail.find_name_and_confirmation_number(ses_msg)
        log.info("Found reservation: {}".format(reservation))
    except Exception as e:
        log.error("Error scraping email {}: {}".format(ses_msg.message_id, e))
        if not ses_msg.from_email.endswith('southwest.com'):
            mail.send_failure_notification(ses_msg.from_email)
        return False

    # Don't add the email if it's straight from southwest.com
    if not ses_msg.from_email.endswith('southwest.com'):
        reservation['email'] = ses_msg.from_email

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
