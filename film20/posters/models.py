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

try:
    from PIL import Image
except:
    import Image

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
try:
    from film20.notification import models as notification
except ImportError:
    notification = None

from film20.core.models import Film
from film20.core.models import Person

from film20.utils.cache_helper import CACHE_FILM, delete_cache
from film20.moderation.models import ModeratedObject

POSTER_DIMENSION = settings.POSTER_DIMENSION
POSTER_MIN_DIMENSION = settings.POSTER_MIN_DIMENSION

def get_image_path( instance, filename ):
    return "tmp_img/objects/%s/%s" % ( filename[0], filename )

class ModeratedPhotoManager( models.Manager ):

    def get_by_object( self, obj ):
        """
        return photos by object ex.
            ModeratedPhoto.objects.get_by_object( Film.objects.get( pk=1 ) )
        """
        content_type = ContentType.objects.get_for_model( obj )
        return self.filter( content_type = content_type, object_id = obj.pk )

class ModeratedPhoto( ModeratedObject ):
    
    content_type = models.ForeignKey( ContentType )
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey( 'content_type', 'object_id' )

    user = models.ForeignKey( User, verbose_name=_( "User", related_name = "added_posters" ) )
    image = models.ImageField( _( "Image" ), upload_to=get_image_path )

    created_at = models.DateTimeField( _( "Created at" ), auto_now_add=True )


    objects = ModeratedPhotoManager()

    class Meta:
        ordering = [ "created_at", "user" ]
        verbose_name = _( "Poster/Photo" )
        verbose_name_plural = _( "Posters/Photos" )
        permissions = (
            # TODO change permission name
            ( "can_accept_posters", "Can accept moderated photos"),
        )

def photo_post_save( sender, instance, created, *args, **kw ):
    
    # resize self image 
    if created:
        image = Image.open( instance.image.path )
        image.thumbnail( POSTER_DIMENSION, Image.ANTIALIAS )
        if image.mode != "RGB":
            image = image.convert( "RGB" )
        image.save( instance.image.path, "JPEG" )

    if isinstance( instance.content_object, Film ) or \
        isinstance( instance.content_object, Person ):
            
            # if accepted, save this photo as main
            if instance.moderation_status == ModeratedPhoto.STATUS_ACCEPTED:
                filename = "%s.jpg" % instance.content_object.permalink[:80]
                
                from film20.useractivity.models import UserActivity

                ua = UserActivity(
                    user=instance.user,
                    username=instance.user.username,
                    activity_type = UserActivity.TYPE_POSTER,
                )

                # in movie hires image is default ...
                if isinstance( instance.content_object, Film ):
                    instance.content_object.hires_image.save( filename, instance.image )

                    ua.film=instance.content_object
                    ua.film_title=instance.content_object.get_title()
                    ua.film_permalink=instance.content_object.permalink
                    ua.content = instance.content_object.hires_image

                else:
                    instance.content_object.image.save( filename, instance.image )
                    
                    # Save:
                    #  person name in object_title
                    #  person permalink in object_slug
                    ua.person = instance.content_object
                    ua.object_title = str( instance.content_object )
                    ua.object_slug = instance.content_object.permalink
                    ua.content = instance.content_object.image

                ua.save()
            
            # if moderated send notification ...
            if instance.moderation_status != ModeratedPhoto.STATUS_UNKNOWN \
               and instance.user != instance.moderation_status_by:
                if notification:
                    notification.send( [ instance.user ], "photo_moderated", { "item": instance, 
                                                                          "status": instance.moderation_status } )

    else:
        raise NotImplementedError

post_save.connect( photo_post_save, sender=ModeratedPhoto )


from film20.config.urls import urls
from film20.moderation.registry import registry
from film20.moderation.items import ModeratedObjectItem

moderated_photo_item = ModeratedObjectItem( 
        ModeratedPhoto, "posters.can_accept_posters",
        name=urls["MODERATED_PHOTOS"], item_template_name="moderation/posters/record.html",
        rss_template_name="moderation/posters/rss.xml"
    )


registry.register( moderated_photo_item )
