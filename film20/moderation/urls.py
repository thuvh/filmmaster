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
from film20.moderation.views import *
from film20.config.urls import *

import film20.moderation.tools.tagging_tools

urlpatterns = patterns( '',   
    url( r'^%s/$' % urls['MODERATION'], index, name='moderation' ),
    url( r'^%s/(?P<model>[\w\-_]+)/$' % urls['MODERATION'], moderate_item, name='moderate-item' ),
    url( r'^%s/(?P<model>[\w\-_]+)/rss/$' % urls['MODERATION'], get_feed, name='moderated-item-rss' ),

    # tag aliases
    url(r'^ajax/tag-aliases/(?P<tag>.*)/$', 'film20.tagging.views.get_tag_aliases' ),
    url(r'^%s/tools/otw/(?P<tag>[\w\-_]+)/$' % urls['MODERATION'], 'film20.tagging.views.objects_tagget_with', name='objects-tagged-with' ),
)
