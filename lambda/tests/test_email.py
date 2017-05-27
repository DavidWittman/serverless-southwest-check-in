import unittest

import mock
import responses

import util

from lib import email


class TestSesMailNotification(unittest.TestCase):

    def setUp(self):
        self.data = util.load_fixture('ses_email_notification')

    def test_from_email(self):
        msg = email.SesMailNotification(self.data)
        assert msg.from_email == "gwb@example.com"

    def test_source(self):
        msg = email.SesMailNotification(self.data)
        assert msg.source == "prvs=31198f0cd=gwb@example.com"
