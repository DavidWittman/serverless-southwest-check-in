import unittest

import mock

import util

from lib import email


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

    @mock.patch('boto3.client')
    def test_send_confirmation_destination(self, mock_client):
        ses_mock = mock.Mock()
        mock_client.return_value = ses_mock
        expected_destination = {'ToAddresses': ['gwb@example.com']}

        email.send_confirmation("gwb@example.com")
        assert ses_mock.send_email.call_args[1]['Destination'] == expected_destination

    @mock.patch('boto3.client')
    def test_send_confirmation_bcc_destination(self, mock_client):
        ses_mock = mock.Mock()
        mock_client.return_value = ses_mock
        expected_destination = {'ToAddresses': ['gwb@example.com'], 'BccAddresses': ['bcc@example.com']}

        email.send_confirmation("gwb@example.com", bcc="bcc@example.com")
        assert ses_mock.send_email.call_args[1]['Destination'] == expected_destination
