import logging
import sys

import swa, exceptions, mail

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def _generate_email_body(response):
    body = "I just checked in to your flight! Please login to Southwest to view your boarding passes.\n"
    for flight in response['checkInConfirmationPage']['flights']:
        body += f"\n{flight['originAirportCode']} => {flight['destinationAirportCode']} (#{flight['flightNumber']})\n"
        for passenger in flight['passengers']:
            # Child and infant fares might check in without a boarding group/position
            if 'boardingGroup' in passenger:
                body += f"  - {passenger['name']}: {passenger['boardingGroup']}{passenger['boardingPosition']}\n"
            else:
                body += f"  - {passenger['name']}\n"
    return body


def main(event, context):
    """
    This function is triggered at check-in time and completes the check-in via
    the Southwest API and emails the reservation, if requested.
    """

    confirmation_number = event['confirmation_number']
    email = event['email']
    first_name = event['first_name']
    last_name = event['last_name']

    log.info("Checking in {} {} ({})".format(
        first_name, last_name, confirmation_number
    ))

    try:
        resp = swa.check_in(first_name, last_name, confirmation_number)
        log.info("Checked in successfully!")
        log.debug("Check-in response: {}".format(resp))
    except exceptions.ReservationNotFoundError:
        log.error("Reservation {} not found. It may have been cancelled".format(confirmation_number))
        raise
    except Exception as e:
        log.error("Error checking in: {}".format(e))
        raise

    # Send success email
    # TODO(dw): This should probably be a separate task in the step function
    subject = "You're checked in!"
    body = "I just checked into your flight! Please login to Southwest to view your boarding passes."

    try:
        body = _generate_email_body(resp)
    except Exception as e:
        log.warning("Error parsing flight details from check-in response: {}".format(e))

    try:
        mail.send_ses_email(email, subject, body)
    except Exception as e:
        log.warning("Error sending email: {}".format(e))

    # Older events use check_in_times.remaining to track remaining check-ins
    # TODO(dw): Remove this when old events are deprecated
    if 'remaining' in event['check_in_times'] and len(event['check_in_times']['remaining']) > 0:
        return False

    return True
