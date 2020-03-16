import os
import unittest

import mock
import vcr

import util

import swa, exceptions

v = vcr.VCR(
    cassette_library_dir=os.path.join(os.path.dirname(__file__), 'fixtures'),
    decode_compressed_response=True
)

@mock.patch('swa.requests')
class TestRequest(unittest.TestCase):
    def test_make_request_get(self, mock_requests):
        expected_headers = {
            "User-Agent": "SouthwestAndroid/7.2.1 android/10",
            "Accept": "application/json",
            "X-API-Key": swa.API_KEY
        }
        expected_url = "https://mobile.southwest.com/api/foo/123456/bar"
        fake_data = ''

        _ = swa._make_request(  # NOQA
            "get",
            "foo/123456/bar",
            fake_data
        )

        mock_requests.get.assert_called_with(expected_url, params=fake_data, headers=expected_headers)

    def test_make_request_post(self, mock_requests):
        expected_headers = {
            "User-Agent": "SouthwestAndroid/7.2.1 android/10",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": swa.API_KEY
        }
        expected_url = "https://mobile.southwest.com/api/foo/123456/bar"
        fake_data = ''

        _ = swa._make_request(  # NOQA
            "post",
            "foo/123456/bar",
            fake_data
        )

        mock_requests.post.assert_called_with(expected_url, json=fake_data, headers=expected_headers)

    def test_make_request_invalid_method(self, mock_requests):
        with self.assertRaises(NotImplementedError):
            swa._make_request("foo", "/foo/123456/bar", {}, "application/json")


class TestCheckIn(unittest.TestCase):

    @v.use_cassette('check_in_success.yml', filter_headers=['X-API-Key'])
    def test_check_in_success(self):
        result = swa.check_in("George", "Bush", "ABC123")
        assert result['checkInConfirmationPage']['flights'][0]['passengers'][0]['name'] == "George W Bush"
        assert result['checkInConfirmationPage']['flights'][0]['passengers'][0]['boardingGroup'] == "A"
        assert result['checkInConfirmationPage']['flights'][0]['passengers'][0]['boardingPosition'] == "33"

    @v.use_cassette('check_in_not_found.yml', filter_headers=['X-API-Key'])
    def test_check_in_reservation_cancelled(self):
        with self.assertRaises(exceptions.ReservationNotFoundError):
            result = swa.check_in("George", "Bush", "ABC123")


class TestReservation(unittest.TestCase):

    @v.use_cassette('view_reservation.yml', filter_headers=['X-API-Key'])
    def test_from_passenger_info(self):
        r = swa.Reservation.from_passenger_info("George", "Bush", "ABC123")
        assert isinstance(r, swa.Reservation)

    @v.use_cassette('view_reservation.yml', filter_headers=['X-API-Key'])
    def test_check_in_times(self):
        r = swa.Reservation.from_passenger_info("George", "Bush", "ABC123")
        assert r.check_in_times == ['2099-08-21T07:35:05-05:00', '2099-08-17T18:50:05-05:00']

    @v.use_cassette('view_reservation_active.yml', filter_headers=['X-API-Key'])
    def test_check_in_times_no_expired(self):
        # this fixture contains one flight which has already occurred
        r = swa.Reservation.from_passenger_info("George", "Bush", "ABC123")
        assert r.check_in_times == ['2099-08-21T07:35:05-05:00']

    @v.use_cassette('view_reservation_active.yml', filter_headers=['X-API-Key'])
    def test_get_check_in_times_with_expired(self):
        # this fixture contains one flight which has already occurred
        r = swa.Reservation.from_passenger_info("George", "Bush", "ABC123")
        assert r.get_check_in_times(expired=True) == ['2099-08-21T07:35:05-05:00', '1999-08-17T18:50:05-05:00']

    @v.use_cassette('view_reservation.yml', filter_headers=['X-API-Key'])
    def test_check_in_times_alternate_second(self):
        r = swa.Reservation.from_passenger_info("George", "Bush", "ABC123")
        r.check_in_seconds = 42
        assert r.check_in_times == ['2099-08-21T07:35:42-05:00', '2099-08-17T18:50:42-05:00']

    @v.use_cassette('view_reservation.yml', filter_headers=['X-API-Key'])
    def test_confirmation_number(self):
        r = swa.Reservation.from_passenger_info("George", "Bush", "ABC123")
        assert r.confirmation_number == "ABC123"
