from django.contrib.auth.models import User
from film20.core.models import Rating, Film
from film20.import_ratings.import_ratings_helper import *
from film20.utils.test import TestCase
class ImportTestCase(TestCase):
    
    def clean_data(self):
        User.objects.all().delete()
        Film.objects.all().delete()
        Rating.objects.all().delete()
        ImportRatings.objects.all().delete()
        ImportRatingsLog.objects.all().delete()

    def tearDown(self):
        self.clean_data()

