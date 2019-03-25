import unittest

import mock
import responses

import util

import swa, exceptions


@mock.patch('swa.requests')
class TestRequest(unittest.TestCase):
    def test_make_request_get(self, mock_requests):
        expected_headers = {
            "User-Agent": "Southwest/4.9.1 CFNetwork/887 Darwin/17.0.0",
            "Content-Type": "application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json",
            "X-Api-Key": swa.API_KEY,
            "Accept-Language": "en-US;q=1"
        }
        expected_url = "https://mobile.southwest.com/api/extensions/v1/mobile/foo/123456/bar"
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
            "User-Agent": "Southwest/4.9.1 CFNetwork/887 Darwin/17.0.0",
            "Content-Type": "application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json",
            "X-Api-Key": swa.API_KEY,
            "Accept-Language": "en-US;q=1"
        }
        expected_url = "https://mobile.southwest.com/api/extensions/v1/mobile/foo/123456/bar"
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


class TestCheckIn(unittest.TestCase):

    def setUp(self):
        self.names = [{
            'firstName': 'George',
            'lastName': 'Bush'
        }]
        self.data = {
            'names': [{
                'firstName': 'George',
                'lastName': 'Bush'
            }]
        }
        self.first_name = "George"
        self.last_name = "Bush"
        self.confirmation_number = "ABC123"
        self.email = "gwb@example.com"

    @mock.patch('swa._make_request')
    def test_check_in_call(self, mock_make_request):
        swa.check_in(self.names, self.confirmation_number)
        mock_make_request.assert_called_with(
            "/reservations/record-locator/ABC123/boarding-passes",
            self.data,
            "application/vnd.swacorp.com.mobile.boarding-passes-v1.0+json"
        )

    @responses.activate
    def test_check_in_success(self):
        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/record-locator/ABC123/boarding-passes',
            json=util.load_fixture('check_in_success'),
            status=200
        )
        result = swa.check_in(self.names, self.confirmation_number)
        assert result['passengerCheckInDocuments'][0]['passenger']['firstName'] == "GEORGE"
        assert result['passengerCheckInDocuments'][0]['passenger']['lastName'] == "BUSH"

    @responses.activate
    def test_check_in_reservation_cancelled(self):
        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/record-locator/ABC123/boarding-passes',
            json=util.load_fixture('check_in_reservation_cancelled'),
            status=404
        )
        with self.assertRaises(exceptions.ReservationNotFoundError):
            result = swa.check_in(self.names, self.confirmation_number)

    @mock.patch('swa._make_request')
    def test_email_boarding_pass(self, mock_make_request):
        fake_data = {
            'names': [{
                'firstName': 'George',
                'lastName': 'Bush'
            }],
            'emailAddress': 'gwb@example.com'
        }

        swa.email_boarding_pass(self.names, self.confirmation_number, self.email)
        mock_make_request.assert_called_with(
            "/record-locator/ABC123/operation-infos/mobile-boarding-pass/notifications",
            fake_data,
            "application/vnd.swacorp.com.mobile.notifications-v1.0+json"
        )



class TestReservation(unittest.TestCase):

    @responses.activate
    def test_from_passenger_info(self):
        responses.add(
            responses.GET,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/record-locator/ABC123',
            json=util.load_fixture('get_reservation'),
            status=200
        )
        r = swa.Reservation.from_passenger_info("George", "Bush", "ABC123")
        assert isinstance(r, swa.Reservation)

    def test_passengers(self):
        fixture = util.load_fixture('get_reservation')
        expected = [{"firstName": "GEORGE", "lastName": "BUSH"}]
        r = swa.Reservation(fixture)
        assert r.passengers == expected

    def test_multiple_passengers(self):
        fixture = util.load_fixture('get_multi_passenger_reservation')
        expected = [
            {"firstName": "GEORGE", "lastName": "BUSH"},
            {"firstName": "LAURA", "lastName": "BUSH"}
        ]
        r = swa.Reservation(fixture)
        assert r.passengers == expected

    def test_check_in_times(self):
        fixture = util.load_fixture('get_reservation')
        r = swa.Reservation(fixture)
        assert r.check_in_times == ['2099-08-21T07:35:05-05:00', '2099-08-17T18:50:05-05:00']

    def test_check_in_times_no_expired(self):
        # The get_active_reservation fixture contains one flight leg which has already occurred
        fixture = util.load_fixture('get_active_reservation')
        r = swa.Reservation(fixture)
        assert r.check_in_times == ['2099-08-21T07:35:05-05:00']

    def test_get_check_in_times_with_expired(self):
        # The get_active_reservation fixture contains one flight leg which has already occurred
        fixture = util.load_fixture('get_active_reservation')
        r = swa.Reservation(fixture)
        assert r.get_check_in_times(expired=True) == ['2099-08-21T07:35:05-05:00', '1999-08-17T18:50:05-05:00']

    def test_check_in_times_alternate_second(self):
        fixture = util.load_fixture('get_reservation')
        r = swa.Reservation(fixture)
        r.check_in_seconds = 42
        assert r.check_in_times == ['2099-08-21T07:35:42-05:00', '2099-08-17T18:50:42-05:00']

    def test_confirmation_number(self):
        fixture = util.load_fixture('get_reservation')
        r = swa.Reservation(fixture)
        assert r.confirmation_number == "ABC123"
