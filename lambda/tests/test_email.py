import unittest

import mock

from collections import namedtuple

import util

from lib import email

class FakeEmail(object):
    def __init__(self, subject, message_id, body=""):
        self.subject = subject
        self.message_id = message_id
        self.body = body

    def body():
        return self.body

class FakeReservation(object):
    confirmation_number = "ABC123"
    check_in_times = ["2017-09-21T07:25:00.000-05:00", "2017-09-28T07:15:00.000-05:00"]

class TestSesMailNotification(unittest.TestCase):

    def setUp(self):
        self.data = util.load_fixture('ses_email_notification')['mail']

    def test_from_email(self):
        msg = email.SesMailNotification(self.data)
        assert msg.from_email == "gwb@example.com"

    def test_source(self):
        msg = email.SesMailNotification(self.data)
        assert msg.source == "prvs=31198f0cd=gwb@example.com"


class TestSendEmail(unittest.TestCase):

    def setUp(self):
        self.reservation = FakeReservation()

    # TODO(dw): This should probably be a send email test as well
    @mock.patch('boto3.client')
    def test_send_confirmation_destination(self, mock_client):
        ses_mock = mock.Mock()
        mock_client.return_value = ses_mock
        expected_destination = {'ToAddresses': ['gwb@example.com']}

        email.send_confirmation("gwb@example.com", self.reservation)
        assert ses_mock.send_email.call_args[1]['Destination'] == expected_destination

    @mock.patch('boto3.client')
    def test_send_ses_email(self, mock_client):
        ses_mock = mock.Mock()
        mock_client.return_value = ses_mock

        expected_msg = {
            'Subject': {
            'Data': 'fake subject',
            'Charset': 'UTF-8'
            },
            'Body': {
            'Text': {
                'Data': 'fake body',
                'Charset': 'UTF-8'
            }
            }
        }
        expected_destination = {'ToAddresses': ['gwb@example.com']}

        email.send_ses_email("gwb@example.com", "fake subject", "fake body", source="wjc@example.com")

        assert ses_mock.send_email.call_args[1]['Source'] == "wjc@example.com"
        assert ses_mock.send_email.call_args[1]['Destination'] == expected_destination
        assert ses_mock.send_email.call_args[1]['Message'] == expected_msg

    @mock.patch('boto3.client')
    def test_send_ses_email_bcc_destination(self, mock_client):
        ses_mock = mock.Mock()
        mock_client.return_value = ses_mock
        expected_destination = {'ToAddresses': ['gwb@example.com'], 'BccAddresses': ['bcc@example.com']}

        email.send_ses_email("gwb@example.com", "fake subject", "fake body", bcc="bcc@example.com")

        assert ses_mock.send_email.call_args[1]['Destination'] == expected_destination

    def test_find_name_and_confirmation_number(self):
        e = FakeEmail('Fwd: Flight reservation (ABC123) | 25FEB18 | AUS-TUL | Bush/George', 0)
        expected = dict(first_name="George", last_name="Bush", confirmation_number="ABC123")
        result = email.find_name_and_confirmation_number(e)
        assert result == expected

    def test_find_name_with_space_and_confirmation_number(self):
        e = FakeEmail('Fwd: Flight reservation (ABC123) | 25FEB18 | AUS-TUL | Mc Lovin/Steven', 0)
        expected = dict(first_name="Steven", last_name="Mc Lovin", confirmation_number="ABC123")
        result = email.find_name_and_confirmation_number(e)
        assert result == expected

    def test_find_new_reservation_email(self):
        e = FakeEmail(
            'Fwd: George Bush\'s 12/25 Boston Logan trip (ABC123): Your reservation is confirmed.',
            0,
            util.load_fixture('new_reservation_email')
        )
        expected = dict(first_name="George", last_name="Bush", confirmation_number="ABC123")
        result = email.find_name_and_confirmation_number(e)
        assert result == expected

    def test_find_new_reservation_email_with_space(self):
        e = FakeEmail(
            'Fwd: Steve Mc Lovin\'s 12/25 Boston Logan trip (ABC123): Your reservation is confirmed.',
            0,
            util.load_fixture('new_reservation_email')
        )
        expected = dict(first_name="Steve", last_name="Mc Lovin", confirmation_number="ABC123")
        result = email.find_name_and_confirmation_number(e)
        assert result == expected
