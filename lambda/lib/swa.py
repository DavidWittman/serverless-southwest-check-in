#
# swa.py
# Functions for interacting with the Southwest API
#

import pendulum
import requests

from . import exceptions

BASE_URL = "https://api-extensions.southwest.com/v1/mobile"
USER_AGENT = "Southwest/3.3.7 (iPhone; iOS 9.3; Scale/2.00)"
# This is not a secret. Well, not my secret at least.
API_KEY = "l7xx8d8bfce4ee874269bedc02832674129b"


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

        raise exceptions.SouthwestAPIError("status_code={} msg=\"{}\"".format(
            response.status_code, msg))

    return response


def _get_check_in_time(departure_time):
    """
    Receives a departure time in RFC3339 format:

        2017-02-09T07:50:00.000-06:00

    And returns the check in time (24 hours prior) as a pendulum time object
    """
    return pendulum.parse(departure_time).subtract(days=1)


def get_check_in_times_from_reservation(reservation):
    """
    Return a sorted and reversed list of check-in times for a reservation as
    RFC3339 timestamps.

    Times are sorted and reversed so that the soonest check-in time may be
    popped from the end of the list.
    """

    flights = reservation['itinerary']['originationDestinations']

    times = [
        _get_check_in_time(segment['departureDateTime']) for flight in flights
        for segment in flight['segments']
    ]

    return list(map(str, reversed(sorted(times))))


def get_reservation(first_name, last_name, confirmation_number):
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

    reservation = response.json()

    return reservation


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

    check_in_docs = response.json()

    return check_in_docs


def email_boarding_pass(first_name, last_name, confirmation_number, email):
    content_type = "application/vnd.swacorp.com.mobile.notifications-v1.0+json"

    data = {
        'names': [{
            'firstName': first_name,
            'lastName': last_name
        }],
        'emailAddress': email
    }

    response = _make_request(
        "/record-locator/%s/operation-infos/mobile-boarding-pass/notifications" % confirmation_number,
        data,
        content_type
    )

    return response.json()
