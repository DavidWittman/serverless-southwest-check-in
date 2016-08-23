import sys

sys.path.append('./vendor')

import requests

BASE_URL = "https://api-extensions.southwest.com/v1/mobile"
USER_AGENT = "Southwest/3.3.7 (iPhone; iOS 9.3; Scale/2.00)"
API_KEY = "l7xx8d8bfce4ee874269bedc02832674129b"


class SouthwestAPIError(Exception):
    pass


def _make_request(path, data, content_type, method='post', check_status_code=True):
    url = "%s%s" % (BASE_URL, path)
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": content_type,
        "X-Api-Key": API_KEY,
        "Accept-Language": "en-US;q=1"
    }

    assert method.lower() in ("post", "get")

    request_fn = getattr(requests, method.lower())
    response = request_fn(url, json=data, headers=headers, verify=False)

    if check_status_code and not response.ok:
        try:
            msg = response.json()['message']
        except:
            msg = response.reason

        raise SouthwestAPIError("status_code=%s msg=\"%s\"" % (response.status_code, msg))

    return response

# TODO(dw): Create a handler wrapper to accept event/context?


def get_reservation(event, context):
    first_name = event['first_name']
    last_name = event['last_name']
    confirmation_number = event['confirmation_number']


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
