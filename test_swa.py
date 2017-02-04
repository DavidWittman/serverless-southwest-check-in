import unittest

import mock
import responses

import swa


class LambdaTester(unittest.TestCase):
    def setUp(self):
        self.event = dict(first_name="George", last_name="Bush", confirmation_number="B2B8TG")
        self.context = "fake context"


@mock.patch('swa.requests')
class TestRequest(LambdaTester):

    def test_make_request_get(self, mock_requests):
        expected_headers = {
            "User-Agent": "Southwest/3.3.7 (iPhone; iOS 9.3; Scale/2.00)",
            "Content-Type": "application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json",
            "X-Api-Key": "l7xx8d8bfce4ee874269bedc02832674129b",
            "Accept-Language": "en-US;q=1"
        }
        expected_url = "https://api-extensions.southwest.com/v1/mobile/foo/123456/bar"
        fake_data = {}

        _ = swa._make_request(  # NOQA
            "/foo/123456/bar",
            fake_data,
            method='get',
            content_type="application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json"
        )

        mock_requests.get.assert_called_with(expected_url, params=fake_data, headers=expected_headers, verify=False)

    def test_make_request_post(self, mock_requests):
        expected_headers = {
            "User-Agent": "Southwest/3.3.7 (iPhone; iOS 9.3; Scale/2.00)",
            "Content-Type": "application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json",
            "X-Api-Key": "l7xx8d8bfce4ee874269bedc02832674129b",
            "Accept-Language": "en-US;q=1"
        }
        expected_url = "https://api-extensions.southwest.com/v1/mobile/foo/123456/bar"
        fake_data = {}

        _ = swa._make_request(  # NOQA
            "/foo/123456/bar",
            fake_data,
            content_type="application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json"
        )

        mock_requests.post.assert_called_with(expected_url, json=fake_data, headers=expected_headers, verify=False)

    def test_make_request_invalid_method(self, mock_requests):
        with self.assertRaises(AssertionError):
            swa._make_request("/foo/123456/bar", {}, "application/json", method="foo")


class TestCheckIn(LambdaTester):

    def setUp(self):
        super(TestCheckIn, self).setUp()
        self.data = {
            'names': [{
                'firstName': 'George',
                'lastName': 'Bush'
            }]
        }
        # TODO(dw): Complete this fixture and move it elsewhere in the test suite
        self.successful_check_in_response = {
            'maxFailedCheckInAttemptsReached': False,
            'passengerCheckInDocuments': [{
                'passenger': {
                    'firstName': 'George',
                    'lastName': 'Bush'
                 },
                'checkinDocuments': [{
                    'boardingGroupNumber': '01',
                    'boardingGroup': 'A',
                    'documentType': 'BOARDING_PASS',
                    'origin': 'AUS',
                    'destination': 'LAS',
                    'flightNumber': '4242'
                }]
            }]
        }

    @mock.patch('swa._make_request')
    def test_check_in_call(self, mock_make_request):
        swa.check_in(self.event, self.context)
        mock_make_request.assert_called_with(
            "/reservations/record-locator/B2B8TG/boarding-passes",
            self.data,
            "application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json"
        )

    @responses.activate
    def test_check_in_success(self):
        responses.add(
            responses.POST,
            'https://api-extensions.southwest.com/v1/mobile/reservations/record-locator/B2B8TG/boarding-passes',
            json=self.successful_check_in_response,
            status=200
        )
        result = swa.check_in(self.event, self.context)
        assert result['message'] == "confirmation_number=%s documents=1 emailed=false" % \
            self.event['confirmation_number']
        assert result['event'] == self.event


class TestReservation(LambdaTester):

    @mock.patch('swa._make_request')
    def test_get_reservation_call(self, mock_make_request):
        fake_data = {
            'action': 'VIEW',
            'first-name': 'George',
            'last-name': 'Bush'
        }

        swa.get_reservation(self.event, self.context)
        mock_make_request.assert_called_with(
            "/reservations/record-locator/B2B8TG",
            fake_data,
            "application/vnd.swacorp.com.mobile.reservations-v1.0+json",
            method='get'
        )

    @responses.activate
    def test_get_reservation_success(self):
        fake_response = {
            'itinerary': {
                'originationDestinations': [{
                    'segments': [{
                        'departureDateTime': '2016-04-16T10:05:00.000-05:00'
                    }]
                }]
            }
        }
        expected_message = "confirmation_number=B2B8TG first_name=\"George\" last_name=\"Bush\" " \
                           "departure_time=2016-04-16T10:05:00.000-05:00"
        responses.add(
            responses.GET,
            'https://api-extensions.southwest.com/v1/mobile/reservations/record-locator/B2B8TG',
            json=fake_response,
            status=200
        )

        result = swa.get_reservation(self.event, self.context)

        assert result['event'] == self.event
        assert result['message'] == expected_message
