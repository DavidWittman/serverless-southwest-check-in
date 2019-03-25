import logging
import unittest

import mock
import responses

import util

import exceptions
from handlers import receive_email, schedule_check_in, check_in

# Prevent the handler function from logging during test runs
logging.disable(logging.CRITICAL)


class TestScheduleCheckIn(unittest.TestCase):

    def setUp(self):
        self.mock_event = {
            'first_name': 'George',
            'last_name': 'Bush',
            'confirmation_number': 'ABC123',
            'email': 'gwb@example.com'
        }

    @mock.patch('mail.send_confirmation')
    @responses.activate
    def test_schedule_check_in(self, email_mock):
        expected = {
            'passengers': [
                {"firstName": "GEORGE", "lastName": "BUSH"}
            ],
            'confirmation_number': 'ABC123',
            'check_in_times': {
                'remaining': ['2099-08-21T07:35:05-05:00'],
                'next': '2099-08-17T18:50:05-05:00'
            },
            'email': 'gwb@example.com'
        }

        responses.add(
            responses.GET,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/record-locator/ABC123',
            json=util.load_fixture('get_reservation'),
            status=200
        )

        result = schedule_check_in(self.mock_event, None)
        assert result == expected

    @mock.patch('mail.send_confirmation')
    @responses.activate
    def test_schedule_multi_passenger_check_in(self, email_mock):
        expected = {
            'passengers': [
                {"firstName": "GEORGE", "lastName": "BUSH"},
                {"firstName": "LAURA", "lastName": "BUSH"},
            ],
            'confirmation_number': 'ABC123',
            'check_in_times': {
                'remaining': ['2099-05-13T15:10:05-05:00'],
                'next': '2099-05-12T08:55:05-05:00'
            },
            'email': 'gwb@example.com'
        }

        responses.add(
            responses.GET,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/record-locator/ABC123',
            json=util.load_fixture('get_multi_passenger_reservation'),
            status=200
        )

        result = schedule_check_in(self.mock_event, None)
        assert result == expected


class TestCheckIn(unittest.TestCase):

    @responses.activate
    def test_multi_passenger_check_in(self):
        fake_event = {
            'passengers': [
                {"firstName": "GEORGE", "lastName": "BUSH"},
                {"firstName": "LAURA", "lastName": "BUSH"},
            ],
            'confirmation_number': 'ABC123',
            'check_in_times': {
                'remaining': [],
                'next': '2017-05-12T08:55:00-05:00'
            },
            'email': 'gwb@example.com'
        }

        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/'
            'record-locator/ABC123/boarding-passes',
            json=util.load_fixture('check_in_success'),
            status=200
        )

        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/record-locator/'
            'ABC123/operation-infos/mobile-boarding-pass/notifications',
            json=util.load_fixture('email_boarding_pass'),
            status=200
        )

        assert(check_in(fake_event, None))

    @responses.activate
    def test_not_last_check_in(self):
        fake_event = {
            'passengers': [
                {"firstName": "GEORGE", "lastName": "BUSH"},
                {"firstName": "LAURA", "lastName": "BUSH"},
            ],
            'confirmation_number': 'ABC123',
            'check_in_times': {
                'remaining': ['2017-05-13T15:10:00-05:00'],
                'next': '2017-05-12T08:55:00-05:00'
            },
            'email': 'gwb@example.com'
        }

        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/'
            'record-locator/ABC123/boarding-passes',
            json=util.load_fixture('check_in_success'),
            status=200
        )

        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/record-locator/'
            'ABC123/operation-infos/mobile-boarding-pass/notifications',
            json=util.load_fixture('email_boarding_pass'),
            status=200
        )

        result = check_in(fake_event, None)
        assert result == False, "check_in response was not False"


    @responses.activate
    def test_old_format_check_in(self):
        fake_event = {
            'first_name': "GEORGE",
            'last_name': "BUSH",
            'confirmation_number': 'ABC123',
            'check_in_times': {
                'remaining': [],
                'next': '2017-05-12T08:55:00-05:00'
            },
            'email': 'gwb@example.com'
        }

        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/'
            'record-locator/ABC123/boarding-passes',
            json=util.load_fixture('check_in_success'),
            status=200
        )

        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/record-locator/'
            'ABC123/operation-infos/mobile-boarding-pass/notifications',
            json=util.load_fixture('email_boarding_pass'),
            status=200
        )

        assert(check_in(fake_event, None))

    @responses.activate
    def test_cancelled_check_in(self):
        fake_event = {
            'first_name': "GEORGE",
            'last_name': "BUSH",
            'confirmation_number': 'ABC123',
            'check_in_times': {
                'remaining': [],
                'next': '2017-05-12T08:55:00-05:00'
            },
            'email': 'gwb@example.com'
        }

        responses.add(
            responses.POST,
            'https://mobile.southwest.com/api/extensions/v1/mobile/reservations/'
            'record-locator/ABC123/boarding-passes',
            json=util.load_fixture('check_in_reservation_cancelled'),
            status=404
        )

        assert(check_in(fake_event, None) == False)

    @responses.activate
    def test_failed_check_in(self):
        pass

