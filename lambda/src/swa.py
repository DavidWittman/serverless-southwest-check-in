#
# swa.py
# Functions for interacting with the Southwest API
#

from urllib.parse import urlencode

import pendulum
import requests

import exceptions

# This is the same User-Agent which update_headers uses
# TODO: Move to a constants file or something so we're not duplicating
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/13.0.5 Safari/605.1.15"
)


def _make_request(method, page, data='', check_status_code=True, headers=None):
    url = f"https://mobile.southwest.com/api/{page}"
    _headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    if headers:
        _headers.update(headers)

    method = method.lower()

    if method == 'get':
        response = requests.get(url, headers=_headers, params=urlencode(data))
    elif method == 'post':
        _headers['Content-Type'] = 'application/json'
        response = requests.post(url, headers=_headers, json=data)
    else:
        raise NotImplementedError()

    if check_status_code and not response.ok:
        try:
            msg = response.json()["message"]
        except Exception:
            msg = response.reason

        if response.status_code == 404:
            raise exceptions.ReservationNotFoundError()
        if response.status_code == 429:
            raise exceptions.TooManyRequestsError()

        raise exceptions.SouthwestAPIError("status_code={} msg=\"{}\"".format(
            response.status_code, msg))

    return response


class Reservation():
    def __init__(self, first_name, last_name, confirmation_number, response):
        self.first_name = first_name
        self.last_name = last_name
        self.confirmation_number = confirmation_number
        self.response = response

        # Second of the minute to use for check in times
        self.check_in_seconds = 5

    def __repr__(self):
        return "<Reservation {}>".format(self.confirmation_number)

    @classmethod
    def from_passenger_info(cls, first_name, last_name, confirmation_number):
        params = {'first-name': first_name, 'last-name': last_name}

        response = _make_request(
            "get",
            "mobile-air-booking/v1/mobile-air-booking/page/view-reservation/" + confirmation_number,
            params
        )

        return cls(first_name, last_name, confirmation_number, response.json())

    def _get_check_in_time(self, departure_time):
        """
        Receives a departure time in RFC3339 format:

            2017-02-09T07:50:00.000-06:00

        And returns the check in time (24 hours prior) as a pendulum time
        object. `self.check_in_seconds` seconds (Default 5) are added to
        the checkin time to allow for some clock skew buffer.
        """
        return pendulum.parse(departure_time)\
            .subtract(days=1)\
            .add(seconds=self.check_in_seconds)

    def get_check_in_times(self, expired=False):
        """
        Return a sorted and reversed list of check-in times for a reservation as
        RFC3339 timestamps. By default, only future checkin times are returned.
        Set `expired` to True to return all checkin times.

        Times are sorted and reversed so that the soonest check-in time may be
        popped from the end of the list.
        """

        flights = self.response['viewReservationViewPage']['shareDetails']['flightInfo']

        times = [
            self._get_check_in_time(flight['departureDateTime'])
            for flight in flights
        ]

        # Remove expired checkins from results
        if not expired:
            times = [t for t in times if t > pendulum.now()]

        return list(map(str, reversed(sorted(times))))

    @property
    def check_in_times(self):
        return self.get_check_in_times()


def check_in(first_name, last_name, confirmation_number, headers):
    # first we get a session token with a GET request, then issue a POST to check in
    page = "mobile-air-operations/v1/mobile-air-operations/page/check-in"
    params = {'first-name': first_name, 'last-name': last_name}

    session = _make_request("get", page + "/" + confirmation_number, params, headers=headers)
    sessionj = session.json()

    try:
        # the whole POST body (including the session token) is provided here
        body = sessionj['checkInViewReservationPage']['_links']['checkIn']['body']
    except KeyError:
        print(sessionj)
        raise exceptions.SouthwestAPIError("Error getting check-in session")

    response = _make_request("post", page, body, headers=headers)
    if not response.ok:
        raise exceptions.SouthwestAPIError("Error checking in! response={}".format(response))

    responsej = response.json()
    if responsej['checkInConfirmationPage']['title']['key'] != 'CHECKIN__YOURE_CHECKEDIN':
        raise exceptions.SouthwestAPIError("Check in failed. response={}".format(responsej))

    return responsej
