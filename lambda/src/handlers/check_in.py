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
        return False
    except Exception as e:
        log.error("Error checking in: {}".format(e))
        raise

    # Return False to indicate that there are check-ins remaining
    if len(event['check_in_times']['remaining']) > 0:
        return False

    return True
