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
# Python
import random
import logging
import pytz, datetime

# Django
from django.utils.translation import gettext_lazy as _, gettext
from django.contrib.auth.models import User
from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

from film20.utils.template import Library
register = Library()


@register.inclusion_tag('facebook_connect/fb_like.html', takes_context=True)
def fb_like(context, object):
    content_type = ContentType.objects.get_for_model(object.__class__)

    return {
        'object':object,
        'content_type':"%s.%s" % (content_type.app_label, content_type.model),
    }

