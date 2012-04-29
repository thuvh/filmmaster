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

class LazyOpenidsAttr(object):
    def __get__(self, request, obj_type=None):
        return request.session.get('openids', [])

class LazyOpenidAttr(object):
    def __get__(self, request, obj_type=None):
        openids = request.session.get('openids')
        return openids and openids[0] or None

class OpenIDMiddleware(object):
    """
    Populate request.openid and request.openids with their openid. This comes 
    eithen from their cookie or from their session, depending on the presence 
    of OPENID_USE_SESSIONS.

    mrk: these attributes are lazy now - original version access session on 
         each request, so Vary: Cookie header is always added and 
         caching pages between clients doesn't work !
    """
    def process_request(self, request):
        request.__class__.openids = LazyOpenidsAttr()
        request.__class__.openid = LazyOpenidAttr()
