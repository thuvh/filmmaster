import os

from django.test.client import Client
from django.utils import unittest

from film20.core.models import Rating, Film, User
from film20.import_ratings.import_ratings_helper import *
from film20.import_ratings.test_import import ImportTestCase

class CritickerImportTestCase(ImportTestCase):

    path = os.path.dirname('')
    vote_history = os.path.abspath('import_ratings/test/test_criticker_rankings.xml')
    def setUp(self):
        Film.objects.filter(imdb_code__lt=1000).delete()

        f1 = Film(type=1, permalink='the-alien', imdb_code=111, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        f1.save()
        f2 = Film(type=1, permalink='the-shawshank-redemption', imdb_code=112, status=1, version=1,
        release_year=1994, title='The Shawshank Redemption', popularity=1, popularity_month=1)
        f2.save()
        f3 = Film(type=1, permalink='terminator-2-judgment-day', imdb_code=113, status=1, version=1,
        release_year=1991, title='Terminator 2: Judgment Day', popularity=1, popularity_month=1)
        f3.save()
        f4 = Film(type=1, permalink='american-history-x', imdb_code=114, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        f4.save()
        f5 = Film(type=1, permalink='the-big-lebowski', imdb_code=115, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        f5.save()
        f6 = Film(type=1, permalink='the-goonies', imdb_code=116, status=1, version=1,
            release_year=1985, title='The Goonies', popularity=1, popularity_month=1)
        f6.save()
        f7 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=117, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: Fellowship of the Ring', popularity=1, popularity_month=1)
        f7.save()

        self.u1=User(username="michuk", email="borys.musielak@gmail.com")
        self.u1.save()

    def test_import(self):
        """
            Import a sample voting history from Criticker XML file
        """

        ratings_list = parse_criticker_votes(self.vote_history)
        self.assertEquals(len(ratings_list),10)

        save_ratings_db(self.u1, ratings_list, ImportRatings.CRITICKER, overwrite=True)

        all_ratings = ImportRatings.objects.all()
        self.assertEquals(len(all_ratings), 1)

        """
            Gets the import records stored in ImportRatings table and
            imports them into single Rating records
        """

        import_ratings()

        ratingsLogs = ImportRatingsLog.objects.all()
        self.assertEquals(len(ratingsLogs), 1)

        ratings = Rating.objects.all()
        self.assertEquals(len(ratings), 10)
