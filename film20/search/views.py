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

from django.utils import simplejson
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from django.http import Http404
from django import http
from film20.tagging.models import Tag
from film20.config.urls import *
from film20.core.search_helper import *
from film20.core.search_forms import *
import logging
logger = logging.getLogger(__name__)

import haystack.views as haystack_views
from haystack.backends import SQ
from haystack.query import SearchQuerySet

from film20.core.models import Film, Person
from film20.search.forms import model_choices, SearchForm
from film20.search.utils import get_model_short_name

class SearchView( haystack_views.SearchView ):    
    def __init__( self, template=templates["SEARCH"], load_all=True, form_class=SearchForm, searchqueryset=None, context_class=RequestContext, limit=None ):
        super( SearchView, self ).__init__( template, load_all, form_class, searchqueryset, context_class )
        self.limit = limit

    def create_response(self):
        """
        Generates the actual HttpResponse to send back to the user.
        """

        facets = []
        try:
            raw_facets = self.results.facet_counts() if self.results else None
            tmp_facets = {}
            if raw_facets is not None:
                for name, length in raw_facets['fields']['django_ct']:
                    if length > 0:
                        results = self.results.narrow( 'django_ct:%s' % name )
                        name = get_model_short_name( name )
                        tmp_facets[name] = {
                            'name': name, 'count': length,
                            'results': results[:self.limit] if self.limit else results
                        }
            
            # sort by default order
            for model, name in model_choices():
                if tmp_facets.has_key( model ):
                    facets.append( tmp_facets[model] )

        except: 
            # on error set empty result
            pass

        context = {
            'query': self.query,
            'model': ''.join( self.form.cleaned_data['t'] ) if self.form.is_valid() else '',
            'form': self.form,
            'full': self.limit is None,
            'facets': facets
        }
        context.update( self.extra_context() )
        
        return render_to_response( self.template, context, context_instance=self.context_class( self.request ) )

def autocomplete( request, limit=10 ):

    try:
        sqs = SearchQuerySet()
       
        # clean query set
        q = sqs.query.clean( request.GET.get( 'term', '' ) )

        sqs = sqs.models( Film, Person )
        # ignore letters
        keywords  = [ k for k in q.split() if len( k ) > 1 ]

        # search word by word
        for keyword in keywords:
            sqs.query.add_filter( SQ( title="%s^2.0" % keyword ) )

        # order by score and popularity
        sqs = sqs.order_by( '-score', '-popularity' )
        
        # add highlight
        sqs = sqs.highlight()

        sqs = sqs[:limit]

    except:
        # on error show empty result 
        sqs = []

    mp = {
        'film': lambda x: { 
            'category'   : 'film', 
            'url'        : x.get_absolute_url(), 
            'value'      : "%s (%s)" % ( x.get_title(), x.release_year ), 
            'description': ','.join( [ str( t ) for t in x.top_directors()[:2] ] ),
            'image'      : x.hires_image.url if x.hires_image else x.image.url if x.image else urls['DEFAULT_POSTER'], 
        },
        'person': lambda x: { 
            'category'   : 'person', 
            'url'        : x.get_absolute_url(), 
            'value'      : '%s %s' % ( x.name, x.surname ), 
            'description': '',
            'image'      : x.image.url if x.image else urls['DEFAULT_ACTOR']
        }
    } 

    content = simplejson.dumps( [ mp[ x.model_name ]( x.object ) for x in sqs ] )
    if 'callback' in request.GET:
        content = "%s(%s)" % ( request.GET['callback'], content )

    return http.HttpResponse( content, mimetype='application/json' )


def search(request):

    best_results = None
    results = None
    search_results = None
    
    if request.method == 'GET':
        search_form = SearchForm(request.GET)
        if search_form.is_valid():            
            search_helper = Search_Helper()
            search_phrase = search_form.cleaned_data['search_phrase']
            
            # FILM
            if search_form.cleaned_data['search_type'] == 'film':
                logger.debug("Szukamy filmu")
                search_results = search_helper.search_film(title=search_phrase)
            # PERSON
            elif search_form.cleaned_data['search_type'] == 'person':
                logger.debug("Szukamy osboy")
                search_results = search_helper.search_person_by_phrase(search_phrase)
            elif search_form.cleaned_data['search_type'] == 'user':
                logger.debug("Szukamy uzytkownika")
                search_results = search_helper.search_user_by_phrase(search_phrase)
            # ALL
            elif search_form.cleaned_data['search_type'] == 'all':
                logger.debug("Szukamy czegokolwiek")
                search_results_film = search_helper.search_film(title=search_phrase)
                search_results_person = search_helper.search_person_by_phrase(search_phrase)
                search_results_user = search_helper.search_user_by_phrase(search_phrase)
                
                # TODO: merging list correctly (btw: what does it mean correctly here?
                search_results = {}
                search_results['best_results'] = list(search_results_film['best_results']) + list(search_results_person['best_results']) + list(search_results_user['best_results'])             
                search_results['results'] = list(search_results_film['results']) + list(search_results_person['results']) + list(search_results_user['results'])
            # UNKNOWN / UNSUPPORTED 
            else:
                logger.debug("Szukamy " + search_form.cleaned_data['search_type'] + " -- not implemented!!!")                
              
            if search_results != None:                  
                best_results = search_results['best_results']
                results = search_results['results']
                logger.debug("Suma wynikow")
                logger.debug(best_results)
    else:
        search_form = SearchForm()
        
    search_film_form = SearchFilmForm()        
    search_person_form = SearchPersonForm()

    context = {            
        'search_form' : search_form,
        'search_film_form' : search_film_form,   
        'search_person_form' : search_person_form,            
        'best_results' : best_results,
        'results' : results,
    }
    return render_to_response(
        templates['SEARCH'], 
        context,
        context_instance=RequestContext(request),
    )
    
def search_film(request, permalink=None, title=None):
    
    # in case we have a form search, set the search criteria
    # (otherwise, we should be getting them as params)    
    
    best_results = None
    results = None
    search_results = None
    search_helper = Search_Helper()
    
    if request.method == 'POST':
        search_film_form = SearchFilmForm(request.POST)
        if search_film_form.is_valid():                             
            title = search_film_form.cleaned_data['title']            
    else:
        search_film_form = SearchFilmForm()           
    
    if ( (title!=None) | (permalink!=None) ):    
        search_results = search_helper.search_film(permalink=permalink, title=title)
        if search_results != None:                  
            best_results = search_results['best_results']
            results = search_results['results']
        
    # other forms
    search_form = SearchForm()
    search_person_form = SearchPersonForm()         
    
    context = {
        'search_form' : search_form,
        'search_film_form' : search_film_form,   
        'search_person_form' : search_person_form,        
        'permalink' : permalink,
        'title' : title,
        'best_results' : best_results,
        'results' : results,
    }   
        
    return render_to_response(
        templates['SEARCH_FILM'], 
        context,
        context_instance=RequestContext(request),
    )

def format_film_row(film,q=None):
  localized = film.get_localized_title()
  disp = "%s / %s"%(film.title,localized) if localized and localized!=film.title else film.title
  title = localized if q and localized and localized.lower().find(q)>=0 else film.title
  title = title.replace('|','&verticalline;')
  disp = disp.replace('|', '&verticalline;')
  return "%s [%d]|%s [%d]|film/%s"%(disp, film.release_year, title, film.release_year, film.permalink)

def format_person_row(person):
  name = "%s %s"%(person.name,person.surname)
  return "%s|%s|osoba/%s"%(name,name,person.permalink)

def search_film_autocomplete(request):
  search_helper = Search_Helper()
  q = request.GET['q'].lower()
  search_results = search_helper.search_film(title=q)
  if search_results != None:
    best_results = search_results['best_results']
    results = search_results['results']
    out = '\n'.join(map(lambda f:format_film_row(f,q), list(best_results)+list(results)))
  else:
    out = ''
  return http.HttpResponse(out, mimetype='text/plain')
    
def search_person(request, permalink=None, person_name=None, person_surname=None):
    
    # in case we have a form search, set the search criteria
    # (otherwise, we should be getting them as params)
    
    best_results = None
    results = None
    search_results = None
    search_helper = Search_Helper()        
    
    if request.method == 'POST':
        search_person_form = SearchPersonForm(request.POST)
        if search_person_form.is_valid():                             
            person_name = search_person_form.cleaned_data['person_name']
            person_surname = search_person_form.cleaned_data['person_surname']     
    else:
        search_person_form = SearchPersonForm()           
    
    if ( (permalink!=None) | (person_name!=None) | (person_surname!=None)):    
        search_results = search_helper.search_person(permalink, person_name, person_surname)
        if search_results != None:                  
            best_results = search_results['best_results']
            results = search_results['results']
        
    # other forms
    search_form = SearchForm()
    search_film_form = SearchFilmForm()         

    context = {
        'search_form' : search_form,
        'search_film_form' : search_film_form,   
        'search_person_form' : search_person_form,                  
        'permalink' : permalink,
        'person_name' : person_name,
        'person_surname' : person_surname,
        'best_results' : best_results,
        'results' : results,
    }
    return render_to_response(
        templates['SEARCH_PERSON'], 
        context,
        context_instance=RequestContext(request),
    )

def search_person_autocomplete(request):
  # sanity check for params (http://jira.filmaster.org/browse/FLM-97)
  if not request.GET.has_key('q'):
      raise Http404
  search_helper = Search_Helper()
  search_results = search_helper.search_person_by_phrase(request.GET['q'])
  if search_results != None:
    best_results = search_results['best_results']
    results = search_results['results']
    out = '\n'.join(map(lambda p:"%s %s"%(p.name,p.surname),list(best_results)+list(results)))
  else:
    out = ''
  return http.HttpResponse(out, mimetype='text/plain')

def search_tag_autocomplete(request):
  # sanity check for params (http://jira.filmaster.org/browse/FLM-97)
  if not request.GET.has_key('q'):
      raise Http404
  
  limit = request.GET.has_key('limit') and request.GET['limit'] or 10
  # TODO: get most popular tags (can be costly)
  tags=Tag.objects.filter(Q(name__istartswith=request.GET['q']), LANG=settings.LANGUAGE_CODE).order_by("name")[:limit];
  out = '\n'.join(map(lambda t:unicode(t),tags))
  return http.HttpResponse(out, mimetype = 'text/plain')

def format_result(ob,q=None):
  return format_film_row(ob,q) if ob.type==1 else format_person_row(ob)

def search_film_person_autocomplete(request):
  # sanity check for params (http://jira.filmaster.org/browse/FLM-97)
  if not request.GET.has_key('q'):
      raise Http404
  
  search_helper = Search_Helper()
  q = request.GET['q'].lower()
  search_results = search_helper.search_film_person_by_phrase(q)
  best_results = search_results['best_results']
  results = search_results['results']
  out = '\n'.join(map(lambda o:format_result(o,q),list(best_results)+list(results)))
  return http.HttpResponse(out, mimetype='text/plain')

def search_user_autocomplete(request):
    if not request.GET.has_key('q'):
        raise Http404
    search_helper = Search_Helper()
    search_results = search_helper.search_user_by_phrase(request.GET['q'])
    if search_results != None:
        best_results = search_results['best_results']
        results = search_results['results']
        out = '\n'.join(map(lambda p:"%s"%(p.username),list(best_results)+list(results)))
    else:
        out = ''
    return http.HttpResponse(out, mimetype='text/plain')

