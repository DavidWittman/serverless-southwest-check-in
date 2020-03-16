import logging
import os
import unittest

import mock
import vcr

import util

import exceptions
from handlers import receive_email, schedule_check_in, check_in

# Prevent the handler function from logging during test runs
logging.disable(logging.CRITICAL)

v = vcr.VCR(
    cassette_library_dir=os.path.join(os.path.dirname(__file__), 'fixtures'),
    decode_compressed_response=True
)


class TestScheduleCheckIn(unittest.TestCase):

    def setUp(self):
        self.mock_event = {
            'first_name': 'George',
            'last_name': 'Bush',
            'confirmation_number': 'ABC123',
            'email': 'gwb@example.com'
        }

    @mock.patch('mail.send_confirmation')
    @v.use_cassette('view_reservation.yml')
    def test_schedule_check_in(self, email_mock):
        expected = {
            'first_name': 'George',
            'last_name': 'Bush',
            'confirmation_number': 'ABC123',
            'check_in_times': [
                '2099-08-21T07:35:05-05:00',
                '2099-08-17T18:50:05-05:00',
            ],
            'email': 'gwb@example.com'
        }

        result = schedule_check_in(self.mock_event, None)
        assert result == expected

    @mock.patch('mail.send_confirmation')
    @v.use_cassette('view_reservation.yml')
    def test_schedule_check_in_without_confirmation_email(self, email_mock):
        self.mock_event['send_confirmation_email'] = False
        schedule_check_in(self.mock_event, None)
        email_mock.assert_not_called()


class TestCheckIn(unittest.TestCase):

    def setUp(self):
        self.fake_event = {
            'first_name': 'George',
            'last_name': 'Bush',
            'confirmation_number': 'ABC123',
            'check_in_times': [
                '2099-08-21T07:35:05-05:00',
                '2099-08-17T18:50:05-05:00',
            ],
            'email': 'gwb@example.com',
            'time': '2099-08-21T07:35:05-05:00'
        }

    @v.use_cassette('check_in_success.yml')
    def test_check_in(self):
        assert(check_in(self.fake_event, None))

    @v.use_cassette('check_in_not_found.yml')
    def test_cancelled_check_in(self):
        with self.assertRaises(exceptions.ReservationNotFoundError):
            check_in(self.fake_event, None)

    @v.use_cassette('check_in_failure.yml')
    def test_failed_check_in(self):
        with self.assertRaises(exceptions.SouthwestAPIError):
            check_in(self.fake_event, None)

