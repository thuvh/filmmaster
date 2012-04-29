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
import datetime

from django.db import models
from django.contrib.auth.models import User

from django_openidconsumer.util import OpenID

class UserOpenID(models.Model):
    user = models.ForeignKey(User)
    openid = models.CharField(max_length=255)
    created_at = models.DateTimeField()

    def __unicode__(self):
        return u"<User %s has OpenID %s>" % (self.user, self.openid)

    class Meta:
        ordering = ('-created_at',)

def associate_openid(user, openid):
    "Associate an OpenID with a user account"
    
    # If this is an OpenID object from the consumer, get the string version
    if isinstance( openid, OpenID ):
        openid = openid.openid

#mrk
    openid = str(openid)
    
    # Remove any matching records first, just in case some slipped through
    unassociate_openid(user, openid)
    
    # Now create the new record
    new = UserOpenID(
        user = user,
        openid = openid,
        created_at = datetime.datetime.now()
    )
    new.save()
    
def unassociate_openid(user, openid):
    "Remove an association between an OpenID and a user account"
    matches = UserOpenID.objects.filter(
        user__id = user.id,
        openid = openid
    )
    [m.delete() for m in matches]
