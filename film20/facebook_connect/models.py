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
from datetime import datetime

from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
import logging
logger = logging.getLogger(__name__)

class FBAssociation(models.Model):
	"""
	Assoction of user accounts and Facebook Accounts
	"""
	user = models.ForeignKey(User, verbose_name=_('User'))
	fb_uid = models.CharField(max_length=100, verbose_name=_('Facebook ID'))
	is_new = models.BooleanField(verbose_name=_('Is new user'), blank=True, default=False)
	is_from_facebook = models.BooleanField(verbose_name=_('Is from Facebook'), default=True, blank=True)
	access_token = models.CharField(max_length=128, verbose_name=_('Facebook Access Token'), null=True, blank=True)
	def __str__(self):
		return str(self.fb_uid)
	def __unicode__(self):
		return str(self.fb_uid)
	class Meta:
		verbose_name = _('Facebook association')
		verbose_name_plural = _('Facebook associations')

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

import json
import urllib2
from urllib import urlencode

class LikeCounter(models.Model):
    likes = models.IntegerField(null=True, blank=True)
    shares = models.IntegerField(null=True, blank=True)
    url = models.URLField(verify_exists=False, unique=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        unique_together = ('content_type', 'object_id')

    def __repr__(self):
        return u"<LikeCounter %r: %s %s>" % (self.object, self.likes, self.shares)

    @classmethod
    def update(cls, url, content_type, object_id):
        app_label, model = content_type.split('.')
        ctype = ContentType.objects.get_by_natural_key(app_label, model)
        object = ctype.get_object_for_this_type(pk=object_id)
        return cls.update_for_object(object)

    @classmethod
    def update_for_object(cls, object):
        url = object.get_absolute_url()

        data = json.loads(urllib2.urlopen(
            'https://graph.facebook.com/?' + urlencode({'ids':url})).read())
        likes = data[url].get('likes')
        shares = data[url].get('shares')

        cnt, created = LikeCounter.objects.get_or_create(
                url=url,
                defaults={
                    'object':object,
                    'likes':likes,
                    'shares':shares,
                })

        if not created:
            cnt.likes = likes
            cnt.shares = shares
            cnt.save()



