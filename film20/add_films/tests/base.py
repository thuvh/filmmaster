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

from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from film20.core.models import Film, Person, Country
from film20.add_films.models import AddedCharacter, AddedFilm

class BaseTest( TestCase ):
    
    def setUp( self ):
        User.objects.all().delete()
        Person.objects.all().delete()
        Country.objects.all().delete()
        AddedFilm.objects.all().delete()
        AddedCharacter.objects.all().delete()

        self.client = Client( follow=True )

        # test user with no permissions
        self.u1 = User.objects.create_user( "user", "user@user.com", "user" )
        
        # test user with moderation_permission
        self.u2 = User.objects.create_user( "root", "root@root.com", "root" )
        self.u2.user_permissions.add( Permission.objects.get( codename="can_accept_added_films" ) )
        self.u2.save()
        
        # some persons
        self.p1 = Person( name="Clint", surname="Eastwood", imdb_code=None, type=Person.TYPE_PERSON  )
        self.p1.save()

        self.p2 = Person( name="Sylwester", surname="Stallone", imdb_code=None, type=Person.TYPE_PERSON  )
        self.p2.save()

        self.p3 = Person( name="Jack", surname="Mort", imdb_code=None, type=Person.TYPE_PERSON  )
        self.p3.save()

        # countries
        self.c1 = Country.objects.create( country='USA' )
        self.c2 = Country.objects.create( country='Poland' )

    def tearDown( self ):
        User.objects.all().delete()
        Person.objects.all().delete()
        Country.objects.all().delete()
        AddedFilm.objects.all().delete()
        AddedCharacter.objects.all().delete()
