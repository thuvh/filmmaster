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
import unittest
from film20.import_ratings.test_filmweb import FilmwebImportTestCase
from film20.import_ratings.test_imdb import IMDBImportTestCase
from film20.import_ratings.test_criticker import CritickerImportTestCase

def suite():
    suite = unittest.TestSuite()

# uncomment the below test when http://jira.filmaster.org/browse/FLM-304 is fixed
    #suite.addTest(FilmwebImportTestCase('test_fetch_votes'))
    suite.addTest(FilmwebImportTestCase('test_import'))

    suite.addTest(CritickerImportTestCase('test_import'))
    suite.addTest(IMDBImportTestCase('test_import'))

    return suite

