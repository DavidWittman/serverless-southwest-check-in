import unittest

import mock

import util

from lib import email

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
