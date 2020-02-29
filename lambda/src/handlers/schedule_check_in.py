import json
import logging

import swa, mail

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def main(event, context):
    """
    This handler looks up the Southwest Reservation via the API to retrieve flight times.

    Returns a dictionary containing details for the rest of the check-in
    """

    # Handle older check-in events TODO(dw): Deprecate this
    # We already have the check-in times, just schedule the next one.
    if 'check_in_times' in event:
        event['check_in_times']['next'] = \
            event['check_in_times']['remaining'].pop()
        return event

    # New check-in, fetch reservation
    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']
    email_address = event.get('email')
    send_confirmation = event.get('send_confirmation_email', True)

    log.info("Looking up reservation {} for {} {}".format(confirmation_number,
                                                          first_name, last_name))
    reservation = swa.Reservation.from_passenger_info(
        first_name, last_name, confirmation_number
    )
    log.debug("Reservation: {}".format(reservation))

    result = {
        'check_in_times': reservation.check_in_times,
        'first_name': first_name,
        'last_name': last_name,
        'confirmation_number': confirmation_number,
        'email': email_address
    }

    # Send a confirmation email
    if email_address and send_confirmation:
        try:
            mail.send_confirmation(email_address, reservation=reservation)
        except Exception as e:
            log.warning("Unable to send confirmation email: {}".format(e))

    return result
