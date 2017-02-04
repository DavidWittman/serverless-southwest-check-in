#
# swa.py
# Functions for interacting with the Southwest API
#

import requests

BASE_URL = "https://api-extensions.southwest.com/v1/mobile"
USER_AGENT = "Southwest/3.3.7 (iPhone; iOS 9.3; Scale/2.00)"
API_KEY = "l7xx8d8bfce4ee874269bedc02832674129b"


class SouthwestAPIError(Exception):
    pass


def _make_request(path, data, content_type, method='post', check_status_code=True):
    """
    Issue a request to the Southwest API

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


def get_itinerary(first_name, last_name, confirmation_number):
    """
    Find detailed origin information from reservation via confirmation number,
    first and last name
    """
    content_type = 'application/vnd.swacorp.com.mobile.reservations-v1.0+json'

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
    itinerary = response.json()

    return itinerary


def check_in(first_name, last_name, confirmation_number):
    content_type = "application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json"

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

    # TODO(dw): error handling
    check_in_docs = response.json()

    return check_in_docs
