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
from datetime import datetime, timedelta, date
import time
import logging
logger = logging.getLogger(__name__)
auth_logger = logging.getLogger('film20.account')

from random import choice

from django.conf import settings
from django.shortcuts import render_to_response
from django.views.generic.simple import direct_to_template
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from film20.core.urlresolvers import reverse as our_reverse
from django.core.urlresolvers import reverse

from film20.facebook_connect.models import *
from film20.userprofile.models import Avatar
from film20.config.urls import *

from django.utils import simplejson as json
import urllib2
from urllib import urlencode
import re
try:
    from PIL import Image
except:
    import Image
import os
import os.path

import base64, pickle

def show_login(request):
    return render_to_response(
        'facebook_connect/show_login.html',
        {},
        context_instance=RequestContext(request))

def get_facebook_cookie(request, app_id, secret):
        import cgi, hashlib
        cookie = request.COOKIES.get('fbs_' + app_id)
        if not cookie:
            return
        parsed = sorted(cgi.parse_qsl(cookie.strip('"')), key=lambda x:x[0])
        ret = dict(parsed)
        s = ''.join("%s=%s"%t for t in parsed if t[0]!='sig')
        if hashlib.md5(s + secret).hexdigest().lower()==ret['sig'].lower():
            return ret

def facebook_user_details(access_token):
    data = dict(
        access_token=access_token,
    )
    me_url = 'https://graph.facebook.com/me?'+urlencode(data)
    reply = json.loads(urllib2.urlopen(me_url).read())
    email = reply.get('email')
    name = reply.get('name')
    uid = reply.get('id')
    
    picture_url = "http://graph.facebook.com/%s/picture?type=large" % uid
    
    return dict(
        email=email,
        username=name,
        avatar_url=picture_url,
        uid=uid,
    )

# non-ajax version of fb_login with registration support
def fb_login2(request):
    # valid cookie retrieved in middleware
    next = request.REQUEST.get('next', '')
    cookie = getattr(request, 'fbcookie', None)

    if not cookie:
        logger.debug("No FB cookie !")
        return HttpResponseRedirect(reverse("acct_login") + "?" + request.META.get("QUERY_STRING", ""))

    uid = cookie['uid']
    access_token = cookie['access_token']
        
    try:
        association = FBAssociation.objects.get(fb_uid=uid)
        if association.access_token != access_token:
             association.access_token = access_token
             association.save()
    except FBAssociation.DoesNotExist:
        # TODO - error handling !
        user_details = facebook_user_details(access_token)
        next = next or full_url('ACCOUNT')
        params = dict(next=next, oauth=request.GET.get('oauth',''))
        details = base64.encodestring(pickle.dumps(user_details)).replace('\n','').strip()
        return HttpResponseRedirect(reverse(fb_register_user, args=[details]) + '?' + urlencode(params))

    user = authenticate(user_id=association.user_id, fb_uid=uid)
    if not user:
        logger.warning("Can't authenticate user")
        return HttpResponse(status=403)
    login(request, user)
    return HttpResponseRedirect(next or "/")

def fb_begin(request):
    qs = base64.encodestring(request.META.get('QUERY_STRING', '')).replace('\n','').rstrip()
    if not qs:
        return HttpResponse(status=400)
    params = dict(
      client_id = settings.FACEBOOK_CONNECT_KEY,
      redirect_uri=settings.FULL_DOMAIN + reverse(fb_auth_cb, args=[qs]),
      display='touch',
      scope='offline_access,publish_stream,create_event,email',
    )
    return HttpResponseRedirect('https://graph.facebook.com/oauth/authorize?' + urlencode(params))

def fb_error(request):
    return direct_to_template(request, 'facebook_connect/fb_error.html', {
        'error_description': "Facebook error: %(descr)s" % {'descr':request.GET.get('descr', '')},
    })

def catch_exception(view):
    def wrapper(request, qs):
        try:
            return view(request, qs)
        except Exception, e:
            qs = base64.decodestring(qs)
            auth_logger.error("Facebook error: %(descr)s" % {'descr':unicode(e)})
            auth_logger.exception(e)
            err = urlencode(dict(descr=unicode(e)))
            return HttpResponseRedirect(reverse(fb_error) + '?' + qs + '&' + err)
    return wrapper

@catch_exception
def fb_auth_cb(request, qs):
    query_string = base64.decodestring(qs)
    if request.GET.get('error'):
        raise Exception(request.GET.get('error_description', 'unknown'))
    params = dict(
        client_id = settings.FACEBOOK_CONNECT_KEY,
        client_secret = settings.FACEBOOK_CONNECT_SECRET,
        redirect_uri=settings.FULL_DOMAIN + reverse(fb_auth_cb, args=[qs]),
        code=request.GET.get('code'),
    )
    url = "https://graph.facebook.com/oauth/access_token?" + urlencode(params)
    access_token = urllib2.urlopen(url).read().split('=')[1]
    user_details = facebook_user_details(access_token)
    uid = user_details['uid']
    try:
        association = FBAssociation.objects.get(fb_uid=uid)
        if association.access_token != access_token:
             association.access_token = access_token
             association.save()
        user = authenticate(user_id=association.user_id, fb_uid=uid)
        login(request, user)
	from urlparse import parse_qs
        next = parse_qs(query_string)['next'][0]
        return HttpResponseRedirect(next)
    except FBAssociation.DoesNotExist, e:
	pass
    
    details = base64.encodestring(pickle.dumps(user_details)).replace('\n','').strip()
    return HttpResponseRedirect(reverse(fb_register_user, args=[details]) + '?' + query_string)

def fb_register_user(request, details):
    from film20.account.views import get_next, new_user_registered_redirect
    from film20.account.forms import SSORegistrationForm
    user_details = pickle.loads(base64.decodestring(details))
    uid = user_details['uid']
    next = get_next(request)
    if request.POST:
        form = SSORegistrationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            assoc = FBAssociation(user=user, fb_uid=uid, is_new=True, is_from_facebook=True)
            assoc.save()
            try:
                Avatar.create_from_url(user, user_details['avatar_url'])
            except Exception, e:
                logger.debug(e)
            user = authenticate(user_id=user.id, fb_uid=uid)
            login(request, user)
            return new_user_registered_redirect(request, next)
    else:
        initial = dict(
            next=next,
            username=user_details.get('username', ''),
            email=user_details.get('email', ''),
        )
        form = SSORegistrationForm(initial=initial)

    return direct_to_template(request, "account/sso_registration.html", {
        'form':form,
        'user_info':user_details,
    })

            

class AssignFacebookForm(forms.Form):
    """
    Assign new OpenID to existing user account using login/password
    """
    login = forms.CharField(label=_("Username"), max_length=30, widget=forms.TextInput({'class':'text'}),)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput({'class':'text', 'render_value':False,}), )

@login_required
def assign_facebook(request):
    """
    Assign new Facebook ID to existing user account using login/password
    """
    error = None
    if not request.facebookconn:
        error = "You are not logged via Facebook Connect"
    else:
        try:
            f = FBAssociation.objects.get(fb_uid=request.facebookconn)
            if not f.is_new or (datetime.now() - f.user.date_joined) > timedelta(days=14):
                error = _("You can reassign only new account")
            elif f.user == request.user:
                # logout (from django only, facebook cookies should survive)
                logout(request)
                return HttpResponseRedirect(reverse(assign_facebook))
        except FBAssociation.DoesNotExist:
            error = _("You are not associated with facebook account")

    if not error:
        assert request.user != f.user and f.is_new
        try:
            f.user.get_profile().delete()
            f.user.delete()
            f.delete()
        except:
            logging.warn(_('No user profile to delete for assign_facebook'))
        # save new Facebook association
        o = FBAssociation(user=request.user, fb_uid=request.facebookconn, is_from_facebook=False)
        o.save()
        request.user.message_set.create(message=_("Successfully assigned with new account"))
        return HttpResponseRedirect('/')

    return render_to_response(
        'facebook_connect/assign_facebook.html',
        {'error': error},
        context_instance=RequestContext(request)
    )

class EditUser(forms.ModelForm):
    """
    Assign new OpenID to existing user account using login/password
    """
    class Meta:
        model = User
        fields = ['username', 'email']


def edit_new_assigned_account(request):
    """
    One-time edit of user login and email after autocreating account by middleware
    """
    if request.facebookconn:
        try:
            f = FBAssociation.objects.get(fb_uid=request.facebookconn)
        except:
            return HttpResponseRedirect("/")
        else:
            if f.is_new == False:
                return HttpResponseRedirect("/")
    
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/")
    
    form =  EditUser(instance=request.user)
    if request.POST:
        form = EditUser(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            f.is_new = False
            f.save()
            return HttpResponseRedirect('/')

    return render_to_response(
        'facebook_connect/edit_new_assigned_account.html',
        {'form': form},
        context_instance=RequestContext(request))

@login_required
def assign_facebook2(request):
    cookie = getattr(request, 'fbcookie', None)
    if not cookie:
        # something wrong, we should have fbcookie here
        return HttpResponse('no facebook cookie', status=403)
    uid = cookie['uid']
    try:
        assoc = FBAssociation.objects.get(user=request.user)
        err = dict(error=_("%s already has fb association") % request.user)
        return HttpResponseRedirect(reverse('associations') + '?' + urlencode(err))
    except FBAssociation.DoesNotExist:
        pass

    try:
        assoc = FBAssociation.objects.get(fb_uid=uid)
        msg=_("This %(service)s service account is already associated with user %(user)s") % dict(service='facebook', user=assoc.user)
        err = dict(error=msg.encode('utf-8'))
        return HttpResponseRedirect(reverse('associations') + '?' + urlencode(err))
    except FBAssociation.DoesNotExist:
        pass
    token = cookie['access_token']
    assoc = FBAssociation.objects.create(
        user=request.user, 
        fb_uid=uid, 
        is_new=False, 
        access_token=token,
        is_from_facebook=False
    )
    return HttpResponseRedirect(reverse('associations') + '?associated')

@login_required
def unassign_facebook(request):
    cookie = getattr(request, 'fbcookie', None)
    if cookie:
        return HttpResponse("Can't remove association if you are logged in with FB")
    FBAssociation.objects.filter(user=request.user).delete()
    return HttpResponseRedirect(reverse('associations') + '?unassociated')

from .models import LikeCounter

from film20.core.deferred import defer

def fb_like(request):
    url = request.POST.get('url')
    content_type=request.POST.get('content_type')
    object_id = request.POST.get('object_id')
    
    if not (url and content_type and object_id):
        return HttpResponse(status=400)
    
    defer(LikeCounter.update, url, content_type, object_id)

    return HttpResponse('ok')


