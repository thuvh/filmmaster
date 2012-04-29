# Create your views here.
import json

from django.template import RequestContext
from django.shortcuts import render, render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User

from film20.config.urls import templates, full_url
from film20.utils.utils import *
from film20.core.models import Film
from film20.core.film_views import show_film
from film20.externallink.models import *
from film20.externallink.forms import *
from django.contrib.auth.decorators import login_required

import re
import logging
logger = logging.getLogger(__name__)
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE

def add_link(request, permalink, ajax=None):
    links = []
    film = None
    if ajax is None and request.method == 'GET':
        if request.user.is_superuser == False:
            film = Film.objects.get(permalink=permalink) 
            links = ExternalLink.objects.filter(film=film, user=request.user, status = ExternalLink.PUBLIC_STATUS)
        else:
            film = Film.objects.get(permalink=permalink) 
            links = ExternalLink.objects.filter(film=film, status = ExternalLink.PUBLIC_STATUS)  
    if request.user.is_authenticated() & (request.method == 'POST'):
        logger.debug("request method is post and user has proper permission")
        form = ExternalLinkForm(request.POST)
        if form.is_valid():
            logger.debug("Form is valid")
            film  = get_object_or_404(Film, permalink=permalink)
            ext_link = form.save(commit=False)
            ext_link.title = form.cleaned_data["title"]
            ext_link.user = request.user
            ext_link.film = film
            ext_link.type = ExternalLink.TYPE_LINK
            ext_link.permalink = ''
            ext_link.version = 1
            ext_link.status = ExternalLink.PUBLIC_STATUS
            ext_link.save(LANG=LANGUAGE_CODE)
            ext_link.save_activity()
            logger.debug("External link is saved")
            if ajax == "json":
                logger.debug("Request was ajax sending response")
                context = {
                    'success': True,
                    'data': ext_link.id,
                }
                return json_return(context)
            form = ExternalLinkForm()
            request.user.message_set.create(message=_("Link added!"))
            data = {
                'film':film,
                'form':form,
                'links':links,
            }
            logger.debug("Request wasn't ajax sending response")
            return render_to_response(templates['ADD_LINKS'], data, context_instance=RequestContext(request))            
        else:
            if ajax=='json':
                logger.debug("Form is invalid sending response in ajax")
                context = {
                    'success': False,
                    'errors': str(form.errors),
                }
                return JSONResponse(context, is_iterable=False)
    form = ExternalLinkForm()
    data = {
        'film':film,
        'form':form,
        'links':links,
    }
    return render_to_response(templates['ADD_LINKS'], data, context_instance=RequestContext(request))

@login_required
def add_video(request, permalink):
    if request.method == 'POST':
        data = {
            'success': False
        }
        the_film  = get_object_or_404(Film, permalink=permalink)
        form = ExternalVideoForm( request.POST, instance=ExternalLink(film=the_film) )
        if form.is_valid():
            logger.debug("Form is valid")
            ext_link = form.save(commit=False)
            ext_link.user = request.user
            ext_link.film = the_film
            ext_link.permalink = 'LINK'
            ext_link.version = 1
            ext_link.type = ExternalLink.TYPE_LINK
            ext_link.status = ExternalLink.PUBLIC_STATUS
            ext_link.url_kind = ExternalLink.TRAILER
            ext_link.moderation_status = ExternalLink.STATUS_UNKNOWN
            pattern =  r"[\\?&]v=([^&#]*)"
            a = re.search(pattern, ext_link.url)
            ext_link.video_thumb = None
            if a is not None:
                video_id = a.group(1)
                ext_link.video_thumb = "http://img.youtube.com/vi/"+video_id+"/2.jpg"
            ext_link.save()
            logger.debug("Video is saved")
 
            # if user has perm to accept video, do this now
            if request.user.has_perm( 'externallink.can_add_link' ):
                ext_link.accept( request.user )
                message = _( "Trailer added!" )
                need_moderate = False

            else: 
                message = _( "Trailer added! awaiting approval" )
                need_moderate = True
           
            data['success'] = True
            data['message'] = message
            data['need_moderate'] = need_moderate
        else:
            data['errors'] = dict([(k, [unicode(e) for e in v]) for k,v in form.errors.items()])
        
        return HttpResponse( json.dumps( data ) )
    return render( request, "movies/movie/add-video.html", { 'form': ExternalVideoForm(),
                                    'permalink': permalink } )


@login_required
def remove_video( request, id ):
    externallink = get_object_or_404( ExternalLink, pk=id )
    url = externallink.get_object_url()
    
    data = { 'success': True };
    
    externallink_to_remove, created = ExternalLinkToRemove.objects.get_or_create( user=request.user, externallink=externallink, 
                                                                                    moderation_status=ExternalLinkToRemove.STATUS_UNKNOWN )
    if request.user.has_perm( 'externallink.can_add_link' ):
        externallink_to_remove.accept( request.user )
        message = _( "Trailer removed!" )
        need_moderate = False

    else: 
        message = _( "Your suggestion to remove this trailer has been received, you will be notified when it's approved by the moderator" )
        need_moderate = True
   
    data['message'] = message
    data['need_moderate'] = need_moderate

    if request.is_ajax():
        return HttpResponse( json.dumps( data ) )
    
    else:
        request.user.message_set.create( message=message )
        return HttpResponseRedirect( url )

@login_required
def remove_link(request, permalink, id):
    try:
        logger.debug("Trying to remove link")
        if request.user.is_superuser == False:
            link = ExternalLink.objects.get(id=id, film__permalink=permalink, user=request.user, status = ExternalLink.PUBLIC_STATUS)
        else:
            link = ExternalLink.objects.get(id=id, film__permalink=permalink, status = ExternalLink.PUBLIC_STATUS)
        link.status = ExternalLink.DELETED_STATUS
        link.save()
        logger.debug("Link is removed redirecting")
        request.user.message_set.create(message=_("Successfully deleted link '%s'") % link.title)
        return HttpResponseRedirect(reverse('film20.externallink.views.add_link',kwargs={ 'permalink': permalink,}))
    except ExternalLink.DoesNotExist:
        logger.debug("Error there is no such link in db")
        return HttpResponseRedirect(reverse("film20.externallink.views.add_link",kwargs={ 'permalink': permalink,}))

def link_partial(request, link_id):
    link = ExternalLink.objects.get(id=link_id)
    data = {'link':link,}
    return render_to_response(
        templates['LINK_PARTIAL'],
        data,
        context_instance=RequestContext(request)
    )
    
def video_partial(request, video_id):
    video = ExternalLink.objects.get(id=video_id)
    data = {'video':video,}
    return render_to_response(
        "video_partial.html", 
        data,
        context_instance=RequestContext(request)
    )            
