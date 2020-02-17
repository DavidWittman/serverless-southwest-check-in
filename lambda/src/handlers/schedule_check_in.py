import json
import logging

import swa, mail

# Set up logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def main(event, context):
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
    email_address = event.get('email')
    send_confirmation = event.get('send_confirmation_email', True)

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

    # Call ourself now that we have some check-in times.
    return main(result, None)
