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
from django import template
from django.utils.html import escape
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.hashcompat import md5_constructor

import urllib

GRAVATAR_URL_PREFIX = getattr(settings, "GRAVATAR_URL_PREFIX", "http://www.gravatar.com/")

register = template.Library()

def get_user(user):
    if not isinstance(user, User):
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            # TODO: make better? smarter? strong? maybe give it wheaties?
            raise Exception, "Bad user for gravatar."
    return user

def gravatar_for_email(email, size=80):
    url = "%savatar/%s/" % (GRAVATAR_URL_PREFIX, md5_constructor(email).hexdigest())
    url += urllib.urlencode({"s": str(size)})
    return escape(url)

def gravatar_for_user(user, size=80):
    user = get_user(user)
    return gravatar_for_email(user.email, size)

def gravatar_img_for_email(email, size=80):
    url = gravatar_for_email(email, size)
    return """<img src="%s" height="%s" width="%s"/>""" % (escape(url), size, size)

def gravatar_img_for_user(user, size=80):
    user = get_user(user)
    url = gravatar_for_user(user)
    return """<img src="%s" alt="Avatar for %s" height="%s" width="%s"/>""" % (escape(url), user.username, size, size)

def gravatar(user, size=80):
    # backward compatibility
    return gravatar_img_for_user(user, size)

register.simple_tag(gravatar)
register.simple_tag(gravatar_for_user)
register.simple_tag(gravatar_for_email)
register.simple_tag(gravatar_img_for_user)
register.simple_tag(gravatar_img_for_email)
