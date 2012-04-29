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

from django.conf.urls.defaults import *
from film20.search.views import *
from film20.config.urls import *

searchpatterns = patterns('',
    url( r'^%s/$' % urls[ "SEARCH" ], SearchView( limit=4 ), name='search' ),
    url( r'^%s-full/$' % urls[ "SEARCH" ], SearchView(), name='search-full' ),    
#    Urls used by old search
#    ### Film search view ###
#    (r'^'+urls["SEARCH_FILM"]+'/$', search_film),
    (r'^ajax/'+urls["SEARCH_FILM"]+'/$', search_film_autocomplete),
#    (r'^'+urls["SEARCH_FILM"]+'/(?P<permalink>[\w\-_]+)/$', search_film),
#
#    ### Person search view ###
#    (r'^'+urls["SEARCH_PERSON"]+'/$', search_person),
    url(r'^ajax/'+urls["SEARCH_PERSON"]+'/$', search_person_autocomplete, name='search_person_autocomplete'),
#    (r'^'+urls["SEARCH_PERSON"]+'/(?P<permalink>[\w\-_]+)/$', search_person),
#    (r'^'+urls["SEARCH_PERSON"]+'/(?P<person_name>[\w\-_]+)/(?P<person_surname>[\w\-_]+)/$', search_person),

    ### User search view ###
    url(r'^ajax/'+urls["SEARCH"]+'/$', search_user_autocomplete, name='search_user_autocomplete'),

    ### tag search ajax service
    url(r'^ajax/search_tag_autocomplete/$', search_tag_autocomplete, name='search_tag_autocomplete'),
    url(r'^ajax/search_film_person_autocomplete/$', search_film_person_autocomplete, name='search_film_person_autocomplete'),
    
    # autocomplete
    url( r'^search/autocomplete/$', autocomplete, name='search-autocomplete' ),    
)
