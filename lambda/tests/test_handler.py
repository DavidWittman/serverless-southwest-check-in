import unittest

import mock
import responses

import handler
import util


class TestScheduleCheckIn(unittest.TestCase):

    def setUp(self):
        self.mock_event = {
            'first_name': 'George',
            'last_name': 'Bush',
            'confirmation_number': 'ABC123',
            'email': 'gwb@aol.com'
        }

    @responses.activate
    def test_schedule_check_in(self):
        expected = {
            'passengers': [
                ("GEORGE", "BUSH")
            ],
            'confirmation_number': 'ABC123',
            'check_in_times': {
                'remaining': ['2017-08-21T07:35:00-05:00'],
                'next': '2017-08-17T18:50:00-05:00'
            },
            'email': 'gwb@aol.com'
        }

        responses.add(
            responses.GET,
            'https://api-extensions.southwest.com/v1/mobile/reservations/record-locator/ABC123',
            json=util.load_fixture('get_reservation'),
            status=200
        )

        result = handler.schedule_check_in(self.mock_event, None)
        assert result == expected

    @responses.activate
    def test_schedule_multi_passenger_check_in(self):
        expected = {
            'passengers': [
                ("GEORGE", "BUSH"),
                ("LAURA", "BUSH")
            ],
            'confirmation_number': 'ABC123',
            'check_in_times': {
                'remaining': ['2017-05-13T15:10:00-05:00'],
                'next': '2017-05-12T08:55:00-05:00'
            },
            'email': 'gwb@aol.com'
        }

        responses.add(
            responses.GET,
            'https://api-extensions.southwest.com/v1/mobile/reservations/record-locator/ABC123',
            json=util.load_fixture('get_multi_passenger_reservation'),
            status=200
        )

        result = handler.schedule_check_in(self.mock_event, None)
        assert result == expected
