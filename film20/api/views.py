from piston import forms
import oauth
from film20.utils.utils import direct_to_template
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.contrib.auth.decorators import login_required

import logging
logger = logging.getLogger('film20.account')

def oauth_auth(request, token, callback, params):
    form = forms.OAuthAuthenticationForm(initial={
        'oauth_token': token.key,
        'authorize_access': True,
        'oauth_callback': token.get_callback_url() or callback,
      })

    return direct_to_template(request, 'piston/authorize_token.html', { 'form': form, 'token': token })

def mobile_stats(request):
    if getattr(request, 'is_mobile', False):
        profile = request.user.get_profile()
        profile.mobile_platform = getattr(request, 'platform', None)
        import datetime
        now = datetime.datetime.now()
        if not profile.mobile_first_login_at:
            profile.mobile_first_login_at = now
        profile.mobile_last_login_at = now
        profile.mobile_login_cnt += 1
        profile.save()
        logger.info("oauth %s login completed, cnt: %s", profile.mobile_platform, profile.mobile_login_cnt)
    else:
        logger.info("oauth login completed")

def login_required2(view):
    def wrapper(request):
        if not request.user.is_authenticated():
            params = dict(
                oauth=1,
                next=request.get_full_path(),
            )
            from django.core.urlresolvers import reverse
            from urllib import urlencode
            return HttpResponseRedirect(reverse('acct_login') + '?' + urlencode(params))
        return view(request)    
    return wrapper
    
@login_required2
def oauth_user_auth(request):
    from piston.authentication import oauth_user_auth as _oauth_user_auth
    response = _oauth_user_auth(request)
    if request.POST:
        if isinstance(response, HttpResponseRedirect):
            if not '?error=' in response['location']:
                mobile_stats(request)
            logger.info("redirect to: %s", response['location'])
        else:
            logger.debug("no redirect")
    else:
        logger.info("waiting for user token authorization...")
    return response

def oauth_pin(request, token):
    from django.http import HttpResponse
    return direct_to_template(request, 'piston/show_pin.html', {'token': token})

def handler404(request):
    return HttpResponseNotFound("not found")

