import logging
import os
import re

import boto3
import pendulum

import exceptions

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


def send_ses_email(to, subject, body, **kwargs):
    """
    Sends an email via SES
    """

    source = kwargs.get('source', os.environ.get('EMAIL_SOURCE'))
    bcc = kwargs.get('bcc', os.environ.get('EMAIL_BCC'))

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
    log.info("Sending email to {}".format(to))

    return ses.send_email(
        Source=source,
        Destination=destination,
        Message=msg
    )


def send_confirmation(to, reservation):
    """
    Sends an email confirming that the user's checkin has been scheduled
    """

    subject = "Your checkin has been scheduled!"
    body = (
        "Thanks for scheduling a checkin for your flight. I will set "
        "my alarm and wake up to check you in 24 hours before your "
        "departure.\n\n"
        "The boarding position which you receive is based on the number of Early Bird "
        "and A-List passengers on your flight. 80%% of checkins are in position B15 or "
        "better, which almost guarantees you won't be stuck with a middle seat. Enjoy your flight!\n\n"
        "Confirmation Number: %s\n"
        "Check-in times:\n"
    ) % (reservation.confirmation_number)

    for c in reversed(reservation.check_in_times):
        pt = pendulum.parse(c)
        body += " - {}\n".format(pt.to_day_datetime_string())

    return send_ses_email(to, subject, body)


def send_failure_notification(to):
    """
    Sends an email when scheduling fails. This usually happens when the email
    format is unrecognized or if there is a problem with the reservation.
    """

    subject = "Error scheduling your checkin"
    body = (
        "There was an error scheduling a checkin for your flight. This usually happens when "
        "I don't recognize the type of email which you sent me. For the best results, forward "
        "the flight reservation email which is sent immediately after booking the flight. "
        "The subject of the email will usually look like one of the following:\n\n"
        "    > Flight reservation (ABC123) | 25DEC18 | MDW-LAX | Smith/John\n"
        "    > Jane Smith's 12/25 Los Angeles trip (ABC123): Your reservation is confirmed.\n\n"
        "If you're still having problems or your email doesn't resemble either of these formats, "
        "send an empty email to me with the following subject line, filling in your name and "
        "confirmation number:\n\n"
        "    > ABC123 John Smith\n\n"
        "When your flight is successfully scheduled, I will send you a friendly email confirming "
        "your checkin times."
    )
    return send_ses_email(to, subject, body)


def find_name_and_confirmation_number(msg):
    """
    Searches through the SES notification for passenger name
    and reservation number.
    """

    fname, lname, reservation = None, None, None

    # Try to match `(5OK3YZ) | 22APR17 | HOU-MDW | Bush/George`
    legacy_email_subject_match = re.search(r"\(([A-Z0-9]{6})\).*\| (\w+ ?\w+\/\w+)", msg.subject)

    # This matches a variety of new email formats which look like
    # George Bush's 12/25 Detroit trip (ABC123)
    new_email_subject_match = re.search(r"(?:[Ff]wd?: )?(\w+).* (\w+)'s.*\(([A-Z0-9]{6})\)", msg.subject)

    # ABC123 George Bush
    manual_email_subject_match = re.search(r"([A-Z0-9]{6})\s+(\w+) (\w+ ?\w+)", msg.subject)

    if legacy_email_subject_match:
        log.debug("Found a legacy reservation email: {}".format(msg.subject))
        reservation = legacy_email_subject_match.group(1)
        lname, fname = legacy_email_subject_match.group(2).split('/')

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

    elif "Passenger Itinerary" in msg.subject:
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

    elif new_email_subject_match:
        log.debug("Found new email subject match: {}".format(msg.subject))
        fname = new_email_subject_match.group(1)
        lname = new_email_subject_match.group(2)
        reservation = new_email_subject_match.group(3)

    elif manual_email_subject_match:
        log.debug("Found manual email subject match: {}".format(msg.subject))
        reservation = manual_email_subject_match.group(1)
        fname = manual_email_subject_match.group(2)
        lname = manual_email_subject_match.group(3)

    # Short circuit we incorrectly match the first name
    # TODO(dw): Remove this when we fix this case in the parser
    if fname in ('Fwd', 'Fw', 'fwd', 'fw'):
        fname = None

    if not all([fname, lname, reservation]):
        raise exceptions.ReservationNotFoundError("Unable to find reservation "
            "in email id {}".format(msg.message_id))

    log.info("Passenger: {} {}, Confirmation Number: {}".format(
        fname, lname, reservation))

    return dict(first_name=fname, last_name=lname, confirmation_number=reservation)
