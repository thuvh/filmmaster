#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
import unittest, os

from django.test.client import Client
from film20.core.models import Rating,Film,User
from film20.import_ratings.import_ratings_helper import *
from film20.import_ratings.test_import import ImportTestCase

class IMDBImportTestCase(ImportTestCase):
    def setUp(self):
        """
        setup user
        """
        self.u1 = User(username='michuk', email='borys.musielak@gmail.com')
        self.u1.save()

        Film.objects.filter(imdb_code__lt=1000).delete()

        f1 = Film(type=1, permalink='we-live-in-public', imdb_code=111, status=1, version=1,
            release_year=2009, title='We live in public', popularity=1, popularity_month=1)
        f1.save()
        # wrong year, should NOT match, only matches when year exact or different by 1
        f2 = Film(type=1, permalink='krotki-film-o-zabijaniu', imdb_code=112, status=1, version=1,
        release_year=1980, title='Krotki film o zabijaniu', popularity=1, popularity_month=1)
        f2.save()
        f3 = Film(type=1, permalink='xiao-cai-feng', imdb_code=113, status=1, version=1,
        release_year=2002, title='Xiao cai feng', popularity=1, popularity_month=1)
        f3.save()
        films = Film.objects.all()
        print "films in database: " + str(len(films))

    def test_import(self):
        """
            Import a sample voting history from Filmweb
        """                

        #setup path to local file with ratings
        f = open('import_ratings/test/test_imdb_ratings.csv', 'rb')
        ratings_list = parse_imdb_votes(f)

        print "parsed ratings_list length=" + str(len(ratings_list))
        self.assertEquals(len(ratings_list), 5)

        save_ratings_db(self.u1, ratings_list, ImportRatings.IMDB, overwrite=True)

        all_ratings = ImportRatings.objects.all()
        self.assertEquals(len(all_ratings), 1)

        """
            Gets the import records stored in ImportRatings table and
            imports them into single Rating records
        """

        import_ratings()

        ratingsLogs = ImportRatingsLog.objects.all()
        self.assertEquals(len(ratingsLogs), 1)
        print ratingsLogs[0]

        films = Film.objects.all()
        print "films in database: " + str(len(films))

        ratings = Rating.objects.all()
        print "imported ratings = " + str(len(ratings))
        self.assertEquals(len(ratings), 5)
