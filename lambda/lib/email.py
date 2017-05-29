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
        self.headers = data['commonHeaders']
        self.subject = self.headers['subject']
        self.source = data['source']

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

    @property
    def from_email(self):
        """
        Cleans the return address provided in the "source" field of the SES
        notification.

        This is primarily used for stripping the BATV signatures, but can
        potentially be used for other sanitizations in the future.
        """

        if self.source.startswith("prvs="):
            # This is a BATV reply address; strip off everything before the
            # prevs=TOKEN= prefix by finding the index of the second =
            index = self.source.index("=", 5) + 1
            return self.source[index:]

        return self.source


def send_confirmation_email(to, **kwargs):
    """
    Sends confirmation email via SES
    """

    source = kwargs.get('source', os.environ.get('EMAIL_SOURCE'))
    bcc = kwargs.get('bcc', os.environ.get('EMAIL_BCC'))

    subject = "Your checkin has been scheduled!"
    body = ("Thanks for scheduling a checkin for your next flight. I will set "
            "my alarm and wake up to check you in 24 hours before your "
            "departure. Fly safe!")

    msg = {
        'Subject': {
            'Data': subject,
            'Charset': 'UTF-8'
        },
        'Body': {
            'Text': {
                'Data': body,
                'Charset': 'UTF-8'
            }
        }
    }

    destination = dict(ToAddresses=[to])
    if bcc:
        destination['BccAddresses'] = [bcc]

    ses = boto3.client('ses')

    log.info("Sending confirmation email to {}".format(to))

    return ses.send_email(
        Source=source,
        Destination=destination,
        Message=msg
    )


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
            log.debug("Passenger matched. Parsing first and last name")
            name_parts = match.group(1).strip().split(' ')
            fname, lname = name_parts[0], name_parts[-1]

    elif "Ticketless Travel Passenger Itinerary" in msg.subject:
        #
        # AIR Confirmation: ABC123
        # *Passenger(s)*
        # BUSH/GEORGE W
        #
        log.debug("Found ticketless itinerary email: {}".format(msg.subject))
        regex = r"AIR Confirmation:\s+([A-Z0-9]{6})\s+\*Passenger\(s\)\*\s+(\w+\/\w+)"
        match = re.search(regex, msg.body())

        if match:
            log.debug("Passenger matched. Parsing first and last name")
            reservation = match.group(1)
            lname, fname = match.group(2).strip().split('/')

    log.info("Passenger: {} {}, Confirmation Number: {}".format(
        fname, lname, reservation))

    if not all([fname, lname, reservation]):
        raise exceptions.ReservationNotFoundError("Unable to find reservation "
            "in email id {}".format(msg.message_id))

    return dict(first_name=fname, last_name=lname, confirmation_number=reservation)
