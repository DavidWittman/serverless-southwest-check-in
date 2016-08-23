#
# swa.py
# Lamba functions for interacting with the Southwest API
#
# TODO(dw): Create a handler wrapper to accept event/context?
#

import sys


# Part of our Lambda deployment process installs requirements into ./vendor, so add it to the path
sys.path.append('./vendor')

import requests  # NOQA

BASE_URL = "https://api-extensions.southwest.com/v1/mobile"
USER_AGENT = "Southwest/3.3.7 (iPhone; iOS 9.3; Scale/2.00)"
API_KEY = "l7xx8d8bfce4ee874269bedc02832674129b"


class SouthwestAPIError(Exception):
    pass


def _make_request(path, data, content_type, method='post', check_status_code=True):
    """Issue a request to the Southwest API

    :param path: The path to send the request to. This should begin with a '/' and not include the base url.
    :param data: Data to send to the server in the HTTP request body.
    :param content_type: Sets the HTTP Content-Type header
    :param method: HTTP method to use. ('post' or 'get')
    :param check_status_code: Raise a SouthwestAPIError if a non-success HTTP status code is returned
    """

    url = "%s%s" % (BASE_URL, path)
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": content_type,
        "X-Api-Key": API_KEY,
        "Accept-Language": "en-US;q=1"
    }

    method = method.lower()
    assert method in ("post", "get")

    if method == "get":
        response = requests.get(url, params=data, headers=headers, verify=False)
    elif method == "post":
        response = requests.post(url, json=data, headers=headers, verify=False)

    if check_status_code and not response.ok:
        try:
            msg = response.json()["message"]
        except:
            msg = response.reason

        raise SouthwestAPIError("status_code=%s msg=\"%s\"" % (response.status_code, msg))

    return response


# TODO(dw): Make this `schedule_check_in`
def get_reservation(event, context):
    """Find detailed origin information from reservation via confirmation number, first and last name."""
    content_type = 'application/vnd.swacorp.com.mobile.reservations-v1.0+json'
    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']

    data = {
        'action': 'VIEW',
        'first-name': first_name,
        'last-name': last_name
    }

    response = _make_request(
        '/reservations/record-locator/%s' % confirmation_number,
        data,
        content_type,
        method="get"
    )

    # TODO(dw): Catch exceptions here and send to failed queue
    departure_time = response.json()['itinerary']['originationDestinations'][0]["segments"][0]["departureDateTime"]

    message = ("confirmation_number=%s first_name=\"%s\" last_name=\"%s\" departure_time=%s"
               % (confirmation_number, first_name, last_name, departure_time))

    return dict(message=message, event=event)


def check_in(event, context):
    content_type = "application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json"
    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']
    data = {
        'names': [{
            'firstName': first_name,
            'lastName': last_name
        }]
    }

    response = _make_request(
        "/reservations/record-locator/%s/boarding-passes" % confirmation_number,
        data,
        content_type
    )

    check_in_docs = response.json()['passengerCheckInDocuments'][0]['checkinDocuments']

    message = "confirmation_number=%s documents=%s emailed=false" % (confirmation_number, len(check_in_docs))
    return dict(message=message, event=event)
