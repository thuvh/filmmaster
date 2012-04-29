from django.utils.translation import gettext as _
from django import template
from film20.account.models import OAUTH_SERVICES
from urllib import urlencode
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

register = template.Library()

def get_next(request):
    login_url = settings.FULL_DOMAIN + reverse('acct_login')
    index_url = settings.FULL_DOMAIN + '/'
    logout_url = settings.FULL_DOMAIN + reverse('acct_logout')
    
    next = request.REQUEST.get('next', '')
    if not next:
        next = 'http://' + request.get_host() + request.get_full_path()
        spath = next.split('?')[0]
        if spath in (login_url, index_url, logout_url):
            return ''
    else:
        if next.startswith('/'):
            next = 'http://' + request.get_host() + next
    params = dict(next=next)
    if 'oauth' in request.GET:
        params['oauth'] = request.GET.get('oauth')
    return mark_safe(urlencode(params))

register.simple_tag(get_next)

@register.simple_tag
def oauth_buttons(request):
    out = []
    for service in OAUTH_SERVICES:
        next = get_next(request)
        ctx = dict(
            name = service.normalized_name,
            url = settings.FULL_DOMAIN + reverse('oauth_login', args=[service.normalized_name]) + '?' + next,
        )
        out.append("<a href='%(url)s' class='%(name)s-button'>%(name)s</a>" % ctx)
    return mark_safe(u''.join(out))
