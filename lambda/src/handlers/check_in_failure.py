import mail


def main(event, context):
    """
    This function is triggered when a check-in fails. It emails a notification
    to the user letting them know that they need to check in manually.
    """

    confirmation_number = event['confirmation_number']
    email = event['email']
    first_name = event['first_name']
    last_name = event['last_name']

    subject = "Error checking in to your flight"
    body = (
        "Sorry! There was an error checking in to your flight. "
        "Please check in to your flight manually to get your boarding passes.\n\n"
        f"First Name: {first_name}\n"
        f"Last Name: {last_name}\n"
        f"Confirmation #{confirmation_number}\n\n"
        "https://www.southwest.com/air/check-in/index.html"
    )
    mail.send_ses_email(email, subject, body)

    # TODO(dw): DRY and move this into a separate task instead of duplicating
    #           here and in the check in handler.
    # Return False to indicate that there are check-ins remaining
    if len(event['check_in_times']['remaining']) > 0:
        return False

    return True
