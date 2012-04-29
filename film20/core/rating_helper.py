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

from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.db import IntegrityError, connection

from film20.config.urls import *
from film20.core.models import Object
from film20.core.models import Film
from film20.core.models import Person
from film20.core.models import Recommendation
from film20.core.models import Rating
from film20.core.models import FilmRanking
from film20.core.rating_form import RatingForm
from film20.recommendations.recom_helper import RecomHelper
from film20.utils import cache
from film20.utils.cache_helper import cache_query
from film20.core.deferred import defer

from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE

import film20.settings as settings
# constants
RECOMMENDATION_ALGORITHM = getattr(settings, "RECOMMENDATION_ALGORITHM", "alg1")

import logging
logger = logging.getLogger(__name__)

# TODO: make internal methods private

class RatingDTO:
    guess_rating = None
    number_of_ratings = None

class BasketsRatingHelper:

    @classmethod
    def _clear_baskets(cls, user):
        for tag in settings.BASKETS_TAGS_LIST:
            cache.delete(cache.Key(cache.CACHE_TAG_BASKET, user, tag))
        cache.delete(cache.Key(cache.CACHE_USER_BASKET, user))
        cache.delete(cache.Key(cache.CACHE_SPECIAL_USER_BASKET, user))

    @classmethod
    def refill_user_baskets(cls, user):
        for tag in settings.BASKETS_TAGS_LIST:
            cls.refill_tag_basket(user, tag)
        cls.refill_user_basket(user)

    @classmethod
    def delete_from_tag_basket(cls, user, id, tag):
        basket_key = cache.Key(cache.CACHE_TAG_BASKET, user, tag)
        tag_basket = cache.get(basket_key) or dict()
        if id in tag_basket:
            tag_basket.pop(id)
        cache.set(basket_key, tag_basket, cache.A_MONTH)
        defer(cls.refill_tag_basket, user, tag)

    @classmethod
    def delete_film_from_baskets_by_id(cls, user, film_id):
        # delete from tag baskets
        for tag in settings.BASKETS_TAGS_LIST:
            cls.delete_from_tag_basket(user, film_id, tag)

        # delete from regular basket
        rating_basket_key = cache.Key(cache.CACHE_USER_BASKET, user)
        rating_basket = cache.get(rating_basket_key) or set()
        rating_basket.discard(film_id)
        cache.set(rating_basket_key, rating_basket, cache.A_MONTH)

        # delete from special basket
        special_rating_basket_key = cache.Key(cache.CACHE_SPECIAL_USER_BASKET,
                user)
        special_rating_basket = cache.get(special_rating_basket_key) or set()
        special_rating_basket.discard(film_id)
        cache.set(special_rating_basket_key, special_rating_basket, cache.A_MONTH)

    @classmethod
    def add_films_to_special_basket_by_film_id(cls, user, film_id):

        NUMBER_RELATED = getattr(settings, 'NUMBER_OF_FILMS_RELATED', 6)
        BASKET_BONUS = getattr(settings, 'SPECIAL_BASKET_BONUS', 4)
        SPECIAL_BASKET_SIZE = getattr(settings, 'SPECIAL_RATE_BASKET_SIZE', 6)
        rating_basket_key = cache.Key(cache.CACHE_USER_BASKET, user)
        special_rating_basket_key = cache.Key(cache.CACHE_SPECIAL_USER_BASKET,
                user)
        rating_basket = cache.get(rating_basket_key) or set()
        special_rating_basket = cache.get(special_rating_basket_key) or set()
        new_basket = []

        try:
            film = Film.objects.get(id=film_id)
            related = cache_query(film.get_related_films()[:NUMBER_RELATED],
                    "film_related_films", film)
        except AttributeError:
            related = []

        if related:
            related = [f.id for f in related]
            new_basket = Film.filter_seen_by_user(user, related)
            new_basket = set(list(new_basket)[:settings.SPECIAL_BASKET_BONUS])

        if new_basket:
            # how many we leave from the previous basket
            left_number = SPECIAL_BASKET_SIZE - len(new_basket)
            basket_list = list(special_rating_basket)

            # we throw old films to normal basket
            rating_basket.update(set(basket_list[left_number:]))
            # we leave some old ones in special basket
            new_basket.update(set(basket_list[:left_number]))

            cache.set(rating_basket_key, rating_basket, cache.A_MONTH)
            cache.set(special_rating_basket_key, new_basket, cache.A_MONTH)

    @classmethod
    def refill_tag_basket(cls, user, tag):

        TAG_BASKET_SIZE = getattr(settings, 'TAG_BASKET_SIZE')
        MIN_TAG_BASKET_SIZE = getattr(settings, 'MIN_TAG_BASKET_SIZE')
        try:
            lang = user.get_profile().LANG
        except AttributeError:
            lang = 'en'

        basket_key = cache.Key(cache.CACHE_TAG_BASKET, user, tag)
        tag_basket = cache.get(basket_key) or dict()

        if len(tag_basket) < MIN_TAG_BASKET_SIZE:
            # get films with this tag
            films_dict = Film.get_film_ids_by_tag(tag, lang)
            # get films seen by user
            seen_films = Film.get_user_seen_films(user)

            # remove films seen by user
            films_dict = dict([(k,v) for k,v in films_dict.items() if k not in seen_films])
            # how many we want to refill
            to_refill = TAG_BASKET_SIZE - len(tag_basket)
            # reverse sort by popularity
            sorted_films = sorted(films_dict, key=films_dict.get, reverse=True)[:to_refill]
            refill_dict = dict([(fid, films_dict[fid]) for fid in sorted_films])

            tag_basket.update(refill_dict)
            cache.set(basket_key, tag_basket, cache.A_MONTH)

    @classmethod
    def get_from_tag_basket(cls, user, tag, number_of_films=1):

        basket_key = cache.Key(cache.CACHE_TAG_BASKET, user, tag)

        no_films_key = cache.Key("no_films_left_for_tag", user, tag)
        # indicates whether there are any films left to show to user
        no_films = cache.get(no_films_key)

        if not no_films:
            tag_basket = cache.get(basket_key) or dict()
            if len(tag_basket) < number_of_films:
                cls.refill_tag_basket(user, tag)
                tag_basket = cache.get(basket_key) or dict()

            result = sorted(tag_basket, key=tag_basket.get,
                    reverse=True)[:number_of_films]

            if not result:
                cache.set(no_films_key, True, cache.A_MONTH)
            else:
                for film_id in result:
                    tag_basket.pop(film_id)
                cache.set(basket_key, tag_basket, cache.A_MONTH)
                defer(cls.refill_tag_basket, user, tag)

            return result
        else:
            return []

    @classmethod
    def refill_user_basket(cls, user):

        BASKET_SIZE = getattr(settings, 'RATE_BASKET_SIZE')
        MIN_BASKET_SIZE = getattr(settings, 'MIN_RATE_BASKET_SIZE')
        rating_basket_key = cache.Key(cache.CACHE_USER_BASKET, user)
        rating_basket = cache.get(rating_basket_key) or set()
        seen_films = Film.get_user_seen_films(user)
        if len(rating_basket) < MIN_BASKET_SIZE:
            while len(rating_basket) < BASKET_SIZE:
                size = len(rating_basket) # we will check if it changes
                for tag in settings.BASKETS_TAGS_LIST:
                    films = cls.get_from_tag_basket(user, tag, number_of_films=1)
                    if films and films[0] not in seen_films:
                        rating_basket.update(films) 
                # if the size hasn't changed
                if len(rating_basket) <= size:
                    break

            cache.set(rating_basket_key, rating_basket, cache.A_MONTH)

    @classmethod
    def get_films_to_rate(cls, user, number_of_films=1, tag=None):

        if not tag:
            rating_basket_key = cache.Key(cache.CACHE_USER_BASKET, user)
            special_rating_basket_key = cache.Key(cache.CACHE_SPECIAL_USER_BASKET,
                    user)
            rating_basket = cache.get(rating_basket_key) or set()
            special_rating_basket = cache.get(special_rating_basket_key) or set()
            rating_basket.difference_update(special_rating_basket)
            if len(rating_basket) + len(special_rating_basket) < number_of_films:
                cls.refill_user_basket(user)
                rating_basket = cache.get(rating_basket_key) or set()
                rating_basket.difference_update(special_rating_basket)

            result = list(special_rating_basket) + list(rating_basket)
            result = result[:number_of_films]
            result_set = set(result)
            rating_basket.difference_update(result_set)
            special_rating_basket.difference_update(result_set)

            cache.set(rating_basket_key, rating_basket, cache.A_MONTH)
            cache.set(special_rating_basket_key,
                    special_rating_basket, cache.A_MONTH)
        else:
            result = cls.get_from_tag_basket(user, tag, number_of_films=number_of_films)

        films = list(Film.objects.filter(id__in=result).select_related())
        return films


def handle_rating(rating_form, user):
    """
    Handles the rating form. Depending on action, calls the insert or update method
    """
    if rating_form.is_valid():                   
        edit_id = rating_form.cleaned_data['edit_id']
        cancel_rating = rating_form.cleaned_data['cancel_rating']
        
        if cancel_rating == 1:
            logger.debug("Cancelling rating...")
            return cancel_rating(rating_form, user)
        else:
            logger.debug("Adding/editing rating...")
            return add_edit_rating(rating_form, user)
    else:
        logger.debug("Rating form invalid!, %s",repr(rating_form.errors))
        return rating_form 

def update_rating_last_displayed(user, film):
    # if not logged in, ignore this
    if user.is_authenticated()==False:
        return
        
    defaults = {
        'last_displayed':datetime.datetime.now(),
        'film':film,
    }
    r, created = Rating.objects.get_or_create(
        user=user,
        parent=film, 
        type=Rating.TYPE_FILM,
        defaults=defaults
    )
    if not created:
        r.last_displayed = defaults['last_displayed']
        r.save()

def add_edit_rating(rating_form, user):
    """
        Creates a new rating for a given object and user based on the rating_form passed.

        Warning: one_rating_for_user_parent_type constraint may be violated if case the
            same method gets called twice with identical parameters and the function
            tries to insert a new rating twice. This is handled quietly, check
            http://jira.filmaster.org/browse/FLM-407 for details.
    """
    rating = rating_form.cleaned_data['rating']    
    object_id = rating_form.cleaned_data['object_id']
    form_type = rating_form.cleaned_data['form_type']
    object = Object.objects.get(id=object_id)            

    rated_object = get_rated_object(form_type, object_id)

    extra = {}
    if rating_form.cleaned_data.get('actor_id',False):
        extra['actor'] = rating_form.cleaned_data['actor_id']
    
    now = datetime.datetime.now()
        
    defaults = {
        'first_rated': now,
        'last_rated': now,
        'rating':rating,
    }

    fkeys = foreign_keys(form_type, rated_object)
    defaults.update(fkeys)
                
    r, created = Rating.objects.get_or_create(
        user=user,
        parent=object,
        type=form_type,
        defaults=defaults,
        **extra
    )
    if not created:
        r.rating = rating
        r.last_rated = now
        r.__dict__.update(fkeys)
        r.save()

    # update the popularity of the rated object
    
    field = {
        Rating.TYPE_ACTOR: 'actor_popularity',
        Rating.TYPE_DIRECTOR: 'director_popularity',
        Rating.TYPE_FILM: 'popularity',
    }.get(form_type, None)

    if field is not None:
        setattr(rated_object, field, (getattr(rated_object, field, 0) or 0) + 1)
        rated_object.save()
        logger.info('%r updated', field)

    return rating_form

def edit_rating(rating_form, user):
    """
    Updates rating for a given object and user basing on the rating_form passed
    """
    rating = rating_form.cleaned_data['rating']    
    object_id = rating_form.cleaned_data['object_id']
    edit_id = rating_form.cleaned_data['edit_id']
    form_type = rating_form.cleaned_data['form_type']
    user_id = user.id

    # Set data depending on the rated object        
    # Check if rated object exists for this parent object
    rated_object = get_rated_object(form_type, object_id)
    
    try:                                
        # save the rating
        r = Rating.objects.get(
            user = user.id, 
            parent = object_id,
            type = form_type,
        )                
        r.rating = rating
        populate_foreign_key(form_type, r, rated_object)
        r.last_rated =  datetime.datetime.now()
        r.save()                       
    except (Rating.DoesNotExist, Rating.MultipleObjectsReturned), e:
        logger.error(unicode(e)) 

    return rating_form

def cancel_rating(rating_form, user):
    """
    Cancels rating for a given object and user basing on the rating_form passed
    """
    rating = rating_form.cleaned_data['rating']    
    object_id = rating_form.cleaned_data['object_id']
    edit_id = rating_form.cleaned_data['edit_id']
    form_type = rating_form.cleaned_data['form_type']
    user_id = user.id

    # Set data depending on the rated object        
    # Check if rated object exists for this parent object
    rated_object = get_rated_object(form_type, object_id)
    logger.debug("rated_object = " + unicode(rated_object))
    
    try:                                
        # save the rating
        r = Rating.objects.get(
            user = user.id, 
            parent = object_id,
            type = form_type,
        )                
        r.rating = None
        populate_foreign_key(form_type, r, rated_object)
        r.last_rated =  datetime.datetime.now()
        logger.debug("r = " + unicode(r))            
        r.save()                       
        
    except (Rating.DoesNotExist, Rating.MultipleObjectsReturned), e:
        logger.error(unicode(e)) 

    return rating_form

def get_ranking(object_id, type=Rating.TYPE_FILM):
    """
        Gets average rating for film in a given category
    """
    query = (                
        Q(film__id = object_id) &
        Q(type = type)
    )
    ranking = FilmRanking.objects.get(query)
    logger.debug("Average ranking for film fetched: " + unicode(ranking.average_score))

    return ranking

def revert_rating(rating):
    if rating != None:
        return 11 - rating
    else:
        return None
    
# TODO - add cache
def guess_score(user, object_id, type=Rating.TYPE_FILM, force_update=False):
    """
        Returns a probable score for a user and an object (e.g. a film) basing
        on others' votes on the same object.
        Depending on the recommendation algorithm used, the rating is taken from a different table
        (core_rating or core_recommendation)
        The probable scores should be updated daily by a cron job running
        bot_helper.do_compute_probable_scores() (old algorithm)
        or the C++ program (new algorithm)
    """
    key = "guess_score_%s_%s_%s" % (getattr(user, 'pk', None), object_id, type)
    score = cache.get(key)
    if score is not None:
        return score
    
    kw = dict(user=user) 

    rating = RatingDTO()
   
    # new algorithm 
    try:
        if RECOMMENDATION_ALGORITHM == "alg2":
            kw.update(dict(
                film=object_id, 
                guess_rating_alg2__isnull = False,
            ))
            current_rating = Recommendation.objects.get(**kw)
            rating.guess_rating = current_rating.guess_rating_alg2
        # old algorithm
        else:
            kw.update(dict(
                parent=object_id, 
                type=type,
                actor__isnull = True,
                director__isnull = True,
                guess_rating_alg1__isnull = False,
            ))
            current_rating = Rating.objects.get(**kw)
            rating.guess_rating = current_rating.guess_rating_alg1
            rating.number_of_ratings = current_rating.number_of_ratings
    except (Rating.DoesNotExist, Recommendation.DoesNotExist), e:
        logger.debug("Could not find a score for user_id=%r and object_id=%r",user, object_id)
        if False and RECOMMENDATION_ALGORITHM == "alg2":
            from film20.recommendations.bot_helper import count_guessed_rate
            profile = user.get_profile()
            if profile.recommendations_status == profile.FAST_RECOMMENDATIONS:
                film = Film.objects.get(parent=object_id)
                recommendation = count_guessed_rate(user, film)
                rating.guess_rating = recommendation.guess_rating_alg2
        
    cache.set(key, rating)
    return rating

def get_rated_object(form_type, object_id):
    # Set data depending on the rated object
    if form_type == Rating.TYPE_ACTOR:
        Type = Person
        query = (
            Q(parent=object_id) &
            Q(is_actor=True)
        )
    elif form_type == Rating.TYPE_DIRECTOR:
        Type = Person
        query = (
            Q(parent=object_id) &
            Q(is_director=True)
        )
    else:
        Type = Film
        query = (
            Q(parent=object_id)
        )
        
    rated_object = Type.objects.get(query)
    return rated_object

def foreign_keys(form_type, rated_object):
    d = {}
    if form_type == Rating.TYPE_ACTOR:
        logger.debug("Setting director to rated_object")
        d['actor'] = rated_object
    elif form_type == Rating.TYPE_DIRECTOR:
        logger.debug("Setting director to rated_object")
        d['director'] = rated_object
    else:                
        logger.debug("Setting film to rated_object")
        d['film'] = rated_object
    return d

def populate_foreign_key(form_type, r, rated_object):
    r.__dict__.update(foreign_keys(form_type, rated_object))
    return r

# FILM DEFAULT FORM    
def get_default_rating_form(object_id, form_type,**extra):
    """
    Returns a default rating form (main one)
    """
    initial= {
      'object_id' : object_id,
      'form_type' : form_type,
      'cancel_rating' : '0',
    }
    initial.update(extra)
    return RatingForm(initial=initial)

def get_rating_form(user_id, object_id, form_type, **extra):
    """
    Returns rating for user, object id and type 
    """
    try:
        # User already rated this movie - populated form
        kwargs = {
         'user':user_id,
         'parent':object_id,
         'type':form_type,
         'normalized__isnull':False
        }
        kwargs.update(extra)
        return Rating.objects.get(**kwargs)
    except Rating.DoesNotExist:
        # User never rated this movie
        return None
    

def generate_rating_form(user_id, object_id, form_type, rating=None, **extra):
    """
    Generates a rating form (main one) for given form for a logged in user
    Returns default form if the user never voted, or an edit form if the user already voted 
    """
#        short_review_text = ""
    
    # User already rated this movie - populated form
    if rating == None:
        return get_default_rating_form(object_id, form_type,**extra)
    initial= {
            'rating' : rating.rating,      
            'edit_id' : rating.id,
            'object_id' : object_id,
            'form_type' : form_type,
            'cancel_rating' : '0',
    }
    initial.update(extra)
    rating_form = RatingForm(initial=initial)                 
     
    return rating_form

# FILM EXTRA FORMS    
def get_default_film_extra_rating_single_form(the_film, rating_type):
    """
    Returns a default film rating form (extra one, for particular type)
    """
    return RatingForm(
        initial= {
            'object_id' : the_film.parent.id,
            'form_type' : rating_type,
        }
    )
    
def get_default_film_rating_extra_forms(the_film):
    """
    Generates the whole list of default extra rating forms for given film
    These do not include actor rating forms, only the extra film parameters rating
    """

    default_film_rating_extra_forms = {}        
    for rating_type in Rating.ADVANCED_RATING_TYPES:
        default_film_rating_extra_forms[rating_type] = get_default_film_extra_rating_single_form(the_film, rating_type)
    return default_film_rating_extra_forms
        
def generate_film_extra_rating_single_form(request, the_film, rating_type):
    """
    Generate a single extra rating parameter rating form for given film and parameter (rating) type for a logged in user
    Returns default form if the user never voted, or an edit form if the user already voted
    """
    try:
        # User already rated this movie - populated form
        rating = Rating.objects.get(
                user = request.user.id, 
                parent = the_film.parent.id,
                type = rating_type,
                actor__isnull = True,
                director__isnull = True,
            )
        film_rating_form = RatingForm(
            initial= {
                'rating' : rating.rating,      
                'edit_id' : rating.id,
                'object_id' : the_film.parent.id,
                'form_type' : rating_type,
                'cancel_rating' : '0',
            }
        )     
        logger.debug("Found value for extra form!")            
    except Rating.DoesNotExist:
        logger.debug("Found NO value for extra form!")
        # User never rated this movie - clear form
        film_rating_form = get_default_film_extra_rating_single_form(the_film, rating_type)
    return film_rating_form

def generate_film_rating_extra_forms(request, the_film):
    """
    Generates the whole list of extra ratings forms for given film
    These do not include actor rating forms, only the extra film parameters rating
    """        
    film_rating_extra_forms = {}        
    for rating_type in Rating.ADVANCED_RATING_TYPES:
        film_rating_extra_forms[rating_type] = generate_film_extra_rating_single_form(request, the_film, rating_type)
    return film_rating_extra_forms

def get_rating_type_label(type):
    # Yes, this is pretty ugly, but it should just work and it's faster than using a hash table 
    # and less coding at the same time (no need to define the same thing twice for 'choices' field in
    # Rating model and for display (michuk) 
    # Generally, this returns the tuple with given ID and takes the second element 
    # from it that should be the display string
    return Rating.ALL_RATING_TYPES[int(type)-1][Rating.INDEX_LABEL]
    
# TODO: properly
def map_extra_forms_to_list(film_rating_extra_forms):
    # if no film form, return null list
    if film_rating_extra_forms==None:
        logger.error("No film_rating_extra_forms found, returning an empty list!")
        return []

    film_rating_extra_forms_as_list = []        
    for rating_type in Rating.ADVANCED_RATING_TYPES:
        film_rating_extra_forms_as_list += {'form':film_rating_extra_forms[rating_type], 'type':rating_type,},
    return film_rating_extra_forms_as_list

def get_movies_to_be_rated_from_session(request):

    films_to_be_rated_user = request.session.get('films_to_be_rated_user', False)

    if films_to_be_rated_user:
        # hack for not-logged-in users
        if request.user.is_authenticated() == False:
            user_id = 1
        else:
            user_id = request.user.id
        if films_to_be_rated_user == user_id:
            if request.session.get('films_to_be_rated', False):
                logger.debug("films_to_be_rated found in session for current user.")
                return request.session['films_to_be_rated']
            else:
                logger.debug("No films_to_be_rated in session for current user.")
                return None
        else:
            logger.debug("Films in session are for a different user!")
            return None
    else:
        logger.debug("No films_to_be_rated_user in session for current user.")
        return None
    
def store_movies_to_be_rated_in_session(request, films_to_be_rated):       
    request.session['films_to_be_rated'] = films_to_be_rated

    # hack for not-logged-in users
    if request.user.is_authenticated() == False:
        user_id = 1
    else:
        user_id = request.user.id

    request.session['films_to_be_rated_user'] = user_id
    
def get_rated_movies_from_session(request):
    if request.session.get('rated_movies', False):            
        return request.session['rated_movies']
    else:           
        return None          
            
def store_rated_movie_in_session(request, object_id):
    rated_movies = [object_id,]
            
    if request.session.get('rated_movies', False):
        logger.debug("Session: rated_movies not is empty:")
        logger.debug(request.session['rated_movies'])
        
        # add the film to the rated list
        request.session['rated_movies'] = request.session['rated_movies'] + rated_movies
    else:                       
        logger.debug("Session: rated_movies is empty")
        request.session['rated_movies'] = rated_movies
        
# TODO: do this randomly, apply some more intelligent logic
def get_random_sorted_ratings(user_id, type=Rating.TYPE_FILM):
    selected_ratings = []
    logger.debug("Fetching random ratings for user...")
    try:            
        qset = (
            Q(user__id=user_id) &
            Q(rating__isnull=False) &
            Q(type=type)
        )
        ratings = Rating.objects.filter(qset).order_by("-rating")            
        ratings_count = ratings.count()
        if ratings_count<11:
            return ratings[:10]
        else:
            # TODO: do this randomly, apply some more intelligent logic
            logger.debug("More ratings than 10, trying heuristics...")
            ratings = list(ratings)
            
            selected_ratings.append(ratings[0])
            selected_ratings.append(ratings[1])
            selected_ratings.append(ratings[(ratings_count/2)-3])
            selected_ratings.append(ratings[(ratings_count/2)-2])
            selected_ratings.append(ratings[(ratings_count/2)-1])
            selected_ratings.append(ratings[ratings_count/2])               
            selected_ratings.append(ratings[ratings_count-5])
            selected_ratings.append(ratings[ratings_count-4])
            selected_ratings.append(ratings[ratings_count-3])
            selected_ratings.append(ratings[ratings_count-2])
                                                          
            return selected_ratings
        
    except Rating.DoesNotExist:
        logger.debug("Rating do not exist?? WTF?")
    
    return None

def get_ratings_for_user_and_film(user, film):
    qset = (
        Q(user = user.id) &
        Q(parent = film.parent.id) &
        Q(rating__isnull=False)
    )
    ratings = Rating.objects.select_related().filter(qset).order_by("type")
    logger.debug("Ratings for author" + unicode(ratings))
    
    map = {}
    for rating in ratings:
        map[rating.type] = rating
            
    return map   

def get_next_film(request):
    """
        Gets next film from session. If list of films to be rated doesn't exist in session, or if there are no 
        more movies to rate, retrieves the list first and then gets next film to rate

    """
    recom_helper = RecomHelper()
    films_to_be_rated = get_movies_to_be_rated_from_session(request)
  
    # hack for not-logged-in users 
    if request.user.is_authenticated() == False:
        user_id = 1
    else:
        user_id = request.user.id

    # logger.debug(films_to_be_rated)
    # just to check if it's session that's causing problems
    # films_to_be_rated = None
    
    # no films to be rated yet
    if films_to_be_rated == None:
        logger.debug("No list of films to be rated found in session, retrieving a new list")
        films_to_be_rated = recom_helper.prepare_films_to_rate(user_id, get_rated_movies_from_session(request))            
        store_movies_to_be_rated_in_session(request, films_to_be_rated)
    # all films rated already
    else:
        len_films = len(films_to_be_rated)
        logger.debug("Film to be rated:" + unicode(len_films))
        if len_films==0:
            logger.debug("All films already rated, retrieving a new list")
            films_to_be_rated = recom_helper.prepare_films_to_rate(user_id, get_rated_movies_from_session(request))            
            store_movies_to_be_rated_in_session(request, films_to_be_rated)
        else:
            logger.debug("Getting next object to rate from session")

    if not films_to_be_rated:
        return None        
    # pop first item from the list
    the_film = films_to_be_rated.pop(0)
    # update the list in session
    store_movies_to_be_rated_in_session(request, films_to_be_rated)
    update_rating_last_displayed(request.user, the_film)
    
    return the_film
