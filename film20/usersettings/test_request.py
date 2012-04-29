from film20.utils.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from film20.usersettings.views import *
from film20.config.urls import *

import logging
logger = logging.getLogger(__name__)

class RequestTestCase(TestCase):

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

    def clean_data(self):
        User.objects.all().delete()

    def test_edit_notification_settings(self):
        """
            Basic test for edit_notification_settings view
        """
        self.initialize()

        self.client.login(username=self.u1.username, password='secret')
        response = self.client.get('/'+urls["SETTINGS"]+'/'+urls["MANAGE_NOTIFICATIONS"]+'/')
        self.failUnlessEqual(response.status_code, 200)


    def test_import_ratings(self):
        """
            Basic test for test_import_ratings view
        """
        self.initialize()
        
        self.client.login(username=self.u1.username, password='secret')
        response = self.client.get('/'+urls["SETTINGS"]+'/'+urls["IMPORT_RATINGS"]+'/')
        self.failUnlessEqual(response.status_code, 200)

    def test_password_change(self):
        """
            Basic test for password_change view
        """
        self.initialize()

        def fetch(user):
            return user.__class__.objects.get(username=user.username)

        self.assertFalse(self.client.login(username=self.u1.username, password='invalidpass'))
        self.assertTrue(self.client.login(username=self.u1.username, password='secret'))

        self.u1.set_unusable_password()
        self.u1.save()

        view = reverse("change_password")

        self.client.post(view, {'password1':'dupa', 'password2': 'blada'})
        
        self.assertFalse(fetch(self.u1).has_usable_password())
        
        self.client.post(view, {'password1':'dupa.8', 'password2': 'dupa.8'})

        self.assertTrue(fetch(self.u1).check_password('dupa.8'))
        
        self.client.post(view, {'oldpassword':'bad', 'password1':'nicepwd', 'password2': 'nicepwd'})
        self.assertFalse(fetch(self.u1).check_password('nicepwd'))

        self.client.post(view, {'oldpassword':'dupa.8', 'password1':'nicepwd', 'password2': 'nicepwd'})
        self.assertTrue(fetch(self.u1).check_password('nicepwd'))
        
        