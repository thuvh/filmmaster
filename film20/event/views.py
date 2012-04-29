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
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect        
from django.template import RequestContext
from django.shortcuts import render_to_response

from film20.event.models import Event, Nominated
from film20.core.rating_form import RatingForm
from film20.core import rating_helper
from film20.utils.utils import *
from film20.config.urls import full_url

from random import shuffle

import logging
logger = logging.getLogger(__name__)

def shuffle_and_extend(itemlist, new_nominated):
    """
        Helper function to be used in show_event to eliminate code redundancy
    """
    shuffle(itemlist)
    new_nominated.extend(itemlist)

def show_event(request, permalink, ajax=None):
  if request.POST:
    if not request.user.is_authenticated():
      if ajax:
        return json_error('LOGIN')
      else:
        return HttpResponseRedirect(full_url('LOGIN') + '?next=%s&reason=vote' % request.path)
    form = rating_helper.handle_rating(RatingForm(request.POST),request.user)
    valid = form.is_valid()
    if ajax:
      return json_success() if valid else json_error("Hmm serwer nawalil?");

  event = get_object_or_404(Event,permalink = permalink)
  nominated = Nominated.objects.with_rates(event)
 
  # randomize lists if event status is open
  if event.event_status == Event.STATUS_OPEN:
    previous_type = -1
    itemlist = []
    new_nominated = []
    for item in nominated:
      current_type = item.oscar_type
      if current_type == previous_type: pass
      elif previous_type==-1: pass
      else:
        shuffle_and_extend(itemlist, new_nominated)
        itemlist = []
      itemlist.append(item)
      previous_type=current_type
    # this shuffles and extends for the last category
    shuffle_and_extend(itemlist, new_nominated)

    # finished!
    nominated = new_nominated

  ctx = {
    'event':event,
    'nominated':nominated
  }

  return render_to_response('event/event.html', ctx, context_instance=RequestContext(request))
