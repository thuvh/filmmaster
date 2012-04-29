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
import ybrowserauth

from django.conf import settings
from django.http import HttpResponseRedirect

def login(request, redirect_to="/invitations/contacts"): # @@@ redirect_to should not be hard-coded here
    ybbauth = ybrowserauth.YBrowserAuth(settings.BBAUTH_APP_ID, settings.BBAUTH_SHARED_SECRET)
    yahoo_login = ybbauth.getAuthURL(appd=redirect_to)
    return HttpResponseRedirect(yahoo_login)

def success(request):
    if "appid" in request.GET:
        ybbauth = ybrowserauth.YBrowserAuth(settings.BBAUTH_APP_ID, settings.BBAUTH_SHARED_SECRET)
        ts = request.GET["ts"]
        sig = request.GET["sig"]
        appdata = request.GET["appdata"]
        REQUEST_URI = request.path + "?" + request.META['QUERY_STRING']
        ybbauth.validate_sig(ts, sig, REQUEST_URI)
        # add token to session for now
        request.session['bbauth_token'] = request.GET["token"]
        return HttpResponseRedirect(appdata)
    else:
        pass # @@@

def logout(request, redirect_to="/"):
    del request.session['bbauth_token']
    return HttpResponseRedirect(redirect_to)
