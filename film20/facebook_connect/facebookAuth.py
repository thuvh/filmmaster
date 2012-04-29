#!/usr/bin/python
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

from django.contrib.auth.models import User
from django.conf import settings

from film20.facebook_connect.models import *

class FacebookBackend(object):
	"""
	Authenticate a user that has associated Facebook to his account
	"""
	def authenticate(self, user_id=False, fb_uid=False):
		if user_id and fb_uid:
			try:
				o = FBAssociation.objects.get(fb_uid=fb_uid, user=User.objects.get(id=user_id))
				return o.user
			except:
				return None
		return None

	def get_user(self, user_id):
		try:
			return User.objects.get(pk=user_id)
		except User.DoesNotExist:
			return None
