import logging
import os
import re

import boto3

from . import exceptions

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class SesMailNotification(object):
    def __init__(self, data, s3_bucket=None):
        self.data = data
        self.subject = data['commonHeaders']['subject']
        self.source = data['source']
        self.from_header = data['commonHeaders']['from']
        self.message_id = data['messageId']
        self._body = None
        # S3 bucket where SES messages are saved to
        if s3_bucket:
            self.s3_bucket = s3_bucket
        else:
            self.s3_bucket = os.getenv('S3_BUCKET_NAME')

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


def find_name_and_confirmation_number(msg):
    """
    Searches through the SES notification for passenger name
    and reservation number.
    """

    fname, lname, reservation = None, None, None

    # Try to match `(5OK3YZ) | 22APR17 | HOU-MDW | Bush/George`
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
        raise exceptions.ReservationNotFoundError("Unable to find reservation "
            "in email id {}".format(msg.message_id))

    return dict(first_name=fname, last_name=lname, confirmation_number=reservation)
