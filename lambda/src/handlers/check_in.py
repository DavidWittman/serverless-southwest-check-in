import logging
import sys

import swa, exceptions

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def main(event, context):
    """
    This function is triggered at check-in time and completes the check-in via
    the Southwest API and emails the reservation, if requested.
    """

    confirmation_number = event['confirmation_number']
    email = event['email']

    # Support older check-ins which did not support multiple passengers
    if "passengers" in event:
        passengers = event['passengers']
    else:
        passengers = [{
            "firstName": event['first_name'],
            "lastName": event['last_name']
        }]

    log.info("Checking in {} ({})".format(
        passengers, confirmation_number
    ))

    try:
        resp = swa.check_in(passengers, confirmation_number)
        log.info("Checked in {} passengers!".format(len(passengers)))
        log.debug("Check-in response: {}".format(resp))
    except exceptions.ReservationNotFoundError:
        log.error("Reservation {} not found. It may have been cancelled".format(confirmation_number))
        return False
    except Exception as e:
        log.error("Error checking in: {}".format(e))
        raise

    log.info("Emailing boarding passes to {}".format(email))
    try:
        swa.email_boarding_pass(passengers, confirmation_number, email)
    except Exception as e:
        log.error("Error emailing boarding pass: {}".format(e))

    # Return False to indicate that there are check-ins remaining
    if len(event['check_in_times']['remaining']) > 0:
        return False

    return True
