#-*- coding: utf-8 -*-
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
# Django
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import Http404
from django.utils import simplejson

# Project
from film20.utils.utils import *
from film20.core.models import *
from film20.core.forms import *
from film20.config.urls import *
from film20.blog.models import Post
from film20.recommendations.recom_helper import RecomHelper
from film20.recommendations.forms import *
from film20.recommendations.forms import get_rating_type_as_int
from film20.useractivity.models import UserActivity
from film20.core.film_helper import FilmHelper
from film20.utils.utils import LazyEncoder
import film20.settings as settings
from film20.utils import cache_helper as cache
from film20.utils.cache_helper import CACHE_ACTIVITIES, KEY_FEATURED, KEY_RECENT

def specs_form(request):
    is_valid = True
    fake_film_specs_form = None
    film_specs_form = None

    if (request.method == 'GET') & ("filter" in request.GET):
        # get generic filter form
        film_specs_form = FilmSpecsForm(request.GET)

        # reset page id for each form submission
        if film_specs_form.has_changed():
            page_id = "1"

        # if valid, check form type and get the correct form submitted
        if film_specs_form.is_valid():
            fake_film_specs_form = __set_filter_form_in_session(film_specs_form, "FilmSpecsForm", request)
            logger.debug("FORM: Film specs type!")
        else:
            is_valid = False
            logger.debug(film_specs_form)
            logger.error("FORM: Filter form invalid!")
    else:
        fake_film_specs_form = FakeFilmSpecsForm()
        film_specs_form = FilmSpecsForm()
        logger.debug("No FORM.")
    return is_valid, fake_film_specs_form, film_specs_form

from django.views.generic.list import ListView
class FilterSpecsForm(ListView):

    def __get_filter_form_from_session(self, name, request):
        tags = None
        year_from = None
        year_to = None
        related_director_as_object = None
        related_director_as_string = None
        related_actor_as_object = None
        related_actor_as_string = None
        popularity = None
        try:
            if request.session.get(name, False):
                tags = request.session.get(name+"__tags", None)
                year_from = request.session.get(name+"__year_from", None)
                year_to = request.session.get(name+"__year_to", None)

                related_director_as_object = request.session.get(name+"__related_director_as_object", None)
                related_director_as_string = request.session.get(name+"__related_director_as_string", None)
                related_actor_as_object = request.session.get(name+"__related_actor_as_object", None)
                related_actor_as_string = request.session.get(name+"__related_actor_as_string", None)
                popularity = request.session.get(name+"__popularity", None)
            else:
                logger.debug(name+" not found in session")
        except KeyError,e:
            logger.error("KeyError -- session key not found!")
            logger.error(e)
        except Exception, e:
            logger.error("Other error!!")
            logger.error(e)
            # just in case, clear the session vars
            request.session[name+"__related_director_as_object"] = None
            request.session[name+"__related_actor_as_object"] = None

        return FakeFilmSpecsForm(
            tags=tags,
            year_from=year_from,
            year_to=year_to,
            related_director_as_string=related_director_as_string,
            related_director_as_object=related_director_as_object,
            related_actor_as_string=related_actor_as_string,
            related_actor_as_object=related_actor_as_object,
            popularity=popularity,
        )

    def __set_filter_form_in_session(self, film_specs_form, name):
        tags = film_specs_form.cleaned_data['tags']
        year_from = film_specs_form.cleaned_data['year_from']
        year_to = film_specs_form.cleaned_data['year_to']
        related_director_as_object = film_specs_form.cleaned_data['related_director']
        related_actor_as_object = film_specs_form.cleaned_data['related_actor']
        popularity = film_specs_form.cleaned_data['popularity']

        related_director_as_string = get_related_people_as_comma_separated_string(related_director_as_object)
        related_actor_as_string = get_related_people_as_comma_separated_string(related_actor_as_object)
        # silly hack
        if tags != None:
            if tags.strip() == '':
                tags = None

        return FakeFilmSpecsForm(
            tags=tags,
            year_from=year_from,
            year_to=year_to,
            related_director_as_string=related_director_as_string,
            related_director_as_object=related_director_as_object,
            related_actor_as_string=related_actor_as_string,
            related_actor_as_object=related_actor_as_object,
            popularity=popularity,
        )

    def __get_initial_film_spec_form(self, saved_form):
        return FilmSpecsForm(
            initial = {
                'tags': saved_form.tags,
                'year_from': saved_form.year_from,
                'year_to': saved_form.year_to,
                'related_director': saved_form.related_director_as_string,
                'related_actor': saved_form.related_actor_as_string,
                'popularity': saved_form.popularity,
            }
        )

    def get_genre(self, **kwargs):
        is_valid, fake_film_specs_form, film_specs_form = self.get_specs_form()
        tags = fake_film_specs_form and fake_film_specs_form.tags
        genre = ''
        genre_key = 'genre'
        if genre_key in self.kwargs:
            genre = self.kwargs['genre']
        if tags:
            if genre:
                genre = genre + ', '
            genre += tags
        return genre

    def get_type(self, **kwargs):
        if 'type_as_str' in self.kwargs:
            type_as_str = get_rating_type_as_int(self.kwargs['type_as_str'])
        else:
            type_as_str = get_rating_type_as_int('film')
        if not type_as_str:
            raise Http404
        return type_as_str

    def get_specs_form(self):
        is_valid = True
        fake_film_specs_form = None
        film_specs_form = None
        if (self.request.method == 'GET') & ("filter" in self.request.GET):
            # get generic filter form
            film_specs_form = FilmSpecsForm(self.request.GET)

            # reset page id for each form submission
            if film_specs_form.has_changed():
                page_id = "1"

            # if valid, check form type and get the correct form submitted
            if film_specs_form.is_valid():
                fake_film_specs_form = self.__set_filter_form_in_session(film_specs_form, "FilmSpecsForm")
                logger.debug("FORM: Film specs type!")
            else:
                is_valid = False
                logger.debug("FORM: Filter form invalid: %r", film_specs_form)
        else:
            fake_film_specs_form = FakeFilmSpecsForm()
            film_specs_form = FilmSpecsForm()
            logger.debug("No FORM.")
        return is_valid, fake_film_specs_form, film_specs_form

    def get_context_data(self, **kwargs):
        context = super(FilterSpecsForm, self).get_context_data(**kwargs)

        genre = self.get_genre()
        default_filter = None
        recom_helper = RecomHelper()
        is_valid, fake_film_specs_form, film_specs_form = self.get_specs_form()

        if is_valid:
            default_filter = fake_film_specs_form.is_empty_form()

        context['film_specs_form'] = film_specs_form
        context['fake_film_specs_form'] = fake_film_specs_form
        context['default_filter'] = default_filter
        context['genre'] = genre
        return context

#TODO: to be refactored (localization of type_as_str)
from film20.core.views import PaginatorListView, UsernameMixin
class RankingListView(PaginatorListView, FilterSpecsForm):
    template_name = templates['RANKING']
    page_size = 10

    def get_context_data(self, **kwargs):
        context = super(RankingListView, self).get_context_data(**kwargs)

        type_as_str = self.get_type()

        context['genre_ranking_str'] = self.get_ranking_label(self.get_genre())
        context['rating_type_str'] = rating_helper.get_rating_type_label(type_as_str)
        context['type_as_str'] = type_as_str
        context['rating_types'] = get_rating_types_to_display()
        return context
    
    # TODO: see why this doesn't work?
    # TODO: is the dic rendered before parsing the gettext?
    def get_ranking_label_dict(self, genre):
        labels = {
            _('comedy'): _('Best comedies'),
        }
        try:
            return labels[genre]
        except KeyError, e:
            # all is fine, just an unsuported genre
            return None

    def get_ranking_label(self, genre):
        if genre == _('action'):
            return _('Best action movies')
        elif genre == _('adventure'):
            return _('Best adventure movies')
        elif genre == _('animation'):
            return _('Best animations')
        elif genre == _('biography'):
            return _('Best biography movies')
        if genre == _('comedy'):
            return _('Best comedy movies')
        elif genre == _('crime'):
            return _('Best crime movies')
        elif genre == _('drama'):
            return _('Best dramas')
        elif genre == _('documentary'):
            return _('Best documentaries')
        elif genre == _('family'):
            return _('Best family movies')
        elif genre == _('fantasy'):
            return _('Best fantasy movies')
        elif genre == _('history'):
            return _('Best history movies')
        elif genre == _('horror'):
            return _('Best horrors')
        elif genre == _('music'):
            return _('Best musicals')
        elif genre == _('mystery'):
            return _('Best mystery movies')
        elif genre == _('romance'):
            return _('Best romance movies')
        elif genre == _('sci-fi'):
            return _('Best science fiction movies')
        elif genre == _('short'):
            return _('Best short movies')
        elif genre == _('sport'):
            return _('Best sport movies')
        elif genre == _('thriller'):
            return _('Best thrillers')
        elif genre == _('war'):
            return _('Best war movies')
        elif genre == _('western'):
            return _('Best westerns')
        else:
            return None

    def get_queryset(self):
        is_valid, fake_film_specs_form, film_specs_form = self.get_specs_form()
        genre = self.get_genre()
        type_as_str = self.get_type()
        recom_helper = RecomHelper()

        tags = genre
        ranking = None

        year_from = None
        year_to = None
        related_director = None
        related_actor = None
        popularity = None
        if is_valid:
            year_from = fake_film_specs_form.year_from
            year_to = fake_film_specs_form.year_to
            related_director = fake_film_specs_form.related_director_as_object
            related_actor = fake_film_specs_form.related_actor_as_object
            popularity = fake_film_specs_form.popularity

        ranking = recom_helper.get_ranking(
            type = type_as_str,
            tags = genre,
            year_from = year_from,
            year_to = year_to,
            related_director = related_director,
            related_actor = related_actor,
            popularity = popularity,
        )
        return ranking

class MoviesMainListView(ListView):
    template_name = templates['MOVIES']
    KEY_FILMS = 'films_reviews'
    KEY_FILM_FEATURED = 'featured_film'

    def get_recent_reviews(self):
        recent_reviews = Post.objects.recent_reviews()
        films = cache.get_cache(CACHE_ACTIVITIES, recent_reviews)
        if not films:
            films = []
            for review in recent_reviews:
                film = review.get_main_related_film()
                films.append(film)
            cache.set_cache(CACHE_ACTIVITIES, recent_reviews, films)
        return recent_reviews, films

    def get_featured_review(self):
        featured_review = Post.objects.featured_review()
        film = cache.get_cache(CACHE_ACTIVITIES, featured_review)
        if not film:
            try:
                film = featured_review.get_main_related_film()
                cache.set_cache(CACHE_ACTIVITIES, featured_review, film)
            except:
                film = []

        return featured_review, film

    def get_context_data(self, **kwargs):
        context = super(MoviesMainListView, self).get_context_data(**kwargs)
        recent_reviews, films  = self.get_recent_reviews()
        featured_review, film = self.get_featured_review()

        context['recent_reviews'] = recent_reviews
        context['featured_review'] = featured_review
        context['films'] = films
        context['featured_film'] = film
        return context

    def get_queryset(self):
        featured_review, film = self.get_featured_review()
        return featured_review

class MoviesGenreListView(PaginatorListView, FilterSpecsForm):
    template_name = templates['MOVIES_GENRE']
    context_object_name = 'films'

    def get_queryset(self):
        genre = self.get_genre()
        is_valid, fake_film_specs_form, film_specs_form = self.get_specs_form()
        recom_helper = RecomHelper()

        year_from = None
        year_to= None
        related_director= None
        related_actor= None
        popularity= None
        if is_valid:
            year_from= fake_film_specs_form.year_from
            year_to= fake_film_specs_form.year_to
            related_director= fake_film_specs_form.related_director_as_object
            related_actor= fake_film_specs_form.related_actor_as_object
            popularity= fake_film_specs_form.popularity

        films = recom_helper.get_films_for_tag(
            tags=genre,
            year_from= year_from,
            year_to= year_to,
            related_director= related_director,
            related_actor= related_actor,
            popularity= popularity
        )
        return films

class ReviewsListView(UsernameMixin, PaginatorListView, FilterSpecsForm):
    template_name = templates['MOVIES_REVIEWS']
    context_object_name = 'reviews'
    NOTES_KEY = 'notes_type'

    def get_notes(self, **kwargs):
        tag = self.get_genre()
        notes_type = []
        if self.NOTES_KEY in self.kwargs:
            notes_type = self.kwargs['notes_type']

        if notes_type == urls['FOLLOWED']:
            reviews = UserActivity.objects.followers_notes(self.user).select_related('film', 'post', 'user')
        elif notes_type == urls['SIMILAR_USERS']:
            reviews = UserActivity.objects.similar_users_notes(self.user).select_related('film', 'post', 'user')
        else:
            reviews = UserActivity.objects.all_notes().select_related('film', 'post', 'user').order_by('-post__publish')
            reviews = reviews.filter(featured=True)

        if tag:
            reviews = reviews.filter(film__objectlocalized__tagged_items__tag__name = tag, film__objectlocalized__LANG = settings.LANGUAGE_CODE)

        return reviews

    def get_context_data(self, **kwargs):
        context = super(ReviewsListView, self).get_context_data(**kwargs)

        context['followed'] = urls['FOLLOWED']
        context['similar_users'] = urls['SIMILAR_USERS']
        return context

    def get_queryset(self):
        self.get_username()
        reviews = self.get_notes()
        return reviews


class RecommendationsListView(PaginatorListView, FilterSpecsForm):
    page_size= 20
    list_of_pages = True
    template_name = templates['MOVIES_RECOMMENDATIONS']
    context_object_name = 'films'

    def get_context_data(self, **kwargs):
        context = super(RecommendationsListView, self).get_context_data(**kwargs)
        default_filter = None
        is_valid, fake_film_specs_form, film_specs_form = self.get_specs_form()

        if is_valid and fake_film_specs_form.tags is not None:
            tags_set = "True"
        else:
            tags_set = "False"

        if self.request.user.is_authenticated():
            recom_status = self.request.user.get_profile().recommendations_status
        else:
            recom_status = False

        context['recom_status'] = recom_status
        context['in_recommendations'] = True
        context['tags_set'] = tags_set
        return context

    def get_queryset(self):
        tags = None
        year_from = None
        year_to = None
        related_director = None
        related_actor = None
        popularity = None
        tags = self.get_genre()

        is_valid, fake_film_specs_form, film_specs_form = \
                self.get_specs_form()

        if is_valid:
            tags = tags
            year_from = fake_film_specs_form.year_from
            year_to = fake_film_specs_form.year_to
            related_director = \
                    fake_film_specs_form.related_director_as_object
            related_actor = fake_film_specs_form.related_actor_as_object
            popularity = fake_film_specs_form.popularity

        films = None
        if self.request.user.is_authenticated():
            recom_status = self.request.user.get_profile().recommendations_status
        else:
            recom_status = False

        if recom_status:
            recom_helper = RecomHelper()
            films = recom_helper.get_best_psi_films_queryset(
                user_id = self.request.user.id,
                tags = tags,
                year_from = year_from,
                year_to = year_to,
                related_director = related_director,
                related_actor = related_actor,
                popularity = popularity,
            )
        else:
            film_helper = FilmHelper()
            films = film_helper.get_best_films(
                tags = tags,
                year_from = year_from,
                year_to = year_to,
                related_director = related_director,
                related_actor = related_actor,
                popularity = popularity
            )

        films = list(films)
        return films

from film20.recommendations.recom_helper import FILMASTER_TYPES, FILMASTERS_ALL, FOLLOWING_ONLY
from film20.recommendations.recom_helper import FILMASTERS_SORT_BY, FILMASTERS_SORT_COMMON_TASTE
def top_users(request, page_id = "1", type=None):
    """
        Lists users with the most common taste, or depending
        on the filtering / sorting criteria, in any other order
    """
            
    form = None
    # boring defaults
    min_common_films = 15
    filmaster_type = FILMASTERS_ALL
    sort_by = FILMASTERS_SORT_COMMON_TASTE
    
    if type == urls['FOLLOWED']:
        followed_page = True
    else:
        followed_page = False
    
    if request.user.is_authenticated():
        this_user = request.user
    else:
        this_user = None
    
    if request.method == "POST":
        # parse the form        
        if followed_page:
            logger.debug("Validating FilmastersForm")
            form = FilmastersForm(request.POST)
        else:
            logger.debug("Validating TopUsersForm")
            form = TopUsersForm(request.POST)
        if form.is_valid():
            logger.debug("TopUsersForm valid")
            min_common_films = form.cleaned_data['min_common_films']
            if not followed_page:
                filmaster_type = form.cleaned_data['filmaster_type']
            sort_by = form.cleaned_data['sort_by']
            # reset page ID
            page_id = "1"
            # and store results into session
            request.session["TopUsersForm"] = True
            request.session["TopUsersForm__min_common_films"] = min_common_films
            if type != urls['FOLLOWED']:
                request.session["TopUsersForm__filmaster_type"] = filmaster_type
            request.session["TopUsersForm__sort_by"] = sort_by
        else:
            logger.error("TopUsersForm invalid")
    elif "TopUsersForm" in request.session:
        # get from session if no form
        try:
            min_common_films = request.session["TopUsersForm__min_common_films"]
            if not followed_page:
                filmaster_type = request.session["TopUsersForm__filmaster_type"]
            sort_by = request.session["TopUsersForm__sort_by"]
        except KeyError:
            # something went wrong (e.g. we updated code to add new variables), reset vars
            request.session["TopUsersForm"] = None
            request.session["TopUsersForm__min_common_films"] = None
            if type != urls['FOLLOWED']:
                request.session["TopUsersForm__filmaster_type"] = None
            request.session["TopUsersForm__sort_by"] = None
        
    
    if form == None:
        logger.debug("Creating a new form with defaults...")
        
        if followed_page:
            logger.debug("Creating new FilmastersForm")
            form = FilmastersForm(
                initial = {
                    'min_common_films': min_common_films,
                    'sort_by': sort_by,
                },
            )
        else:
            logger.debug("Creating new TopUsersForm")
            form = TopUsersForm(
                initial = {
                    'min_common_films': min_common_films,
                    'filmaster_type': filmaster_type,
                    'sort_by': sort_by,
                },
            )
            
    if followed_page:
        filmaster_type = FOLLOWING_ONLY
    
    recom_helper = RecomHelper()        
    best_tci_users = recom_helper.get_best_tci_users(          
        user = this_user, 
        min_common_films = min_common_films,
        filmaster_type = filmaster_type,
        sort_by = sort_by,
    )

    logger.debug(form)
    context = {
        "object_list" : best_tci_users,
        "form": form,
        "followed_page": followed_page,
    }

    return render_to_response(templates['TOP_USERS'],
            context,
            context_instance=RequestContext(request))    

def show_tag_page(request, tag, festival = None):
    """
        Shows a tag page with a list of recent activities for movies tagged with the
        selected tag, its ranking and film recommendations for the tag (for logged in users)
        This is also used for film festival sites as festivals use tags to group films 
        (show_tag_page caled from festivals.views.show_festival)
    """
       
    if tag == None:
        raise Http404

    recom_helper = RecomHelper()
    ranking = recom_helper.get_ranking(
        type = Rating.TYPE_FILM,
        tags = tag,
        limit = 25, # TODO: customize
        offset = 0,
        festival = festival,
    )

    recommended_films = None
    if request.user.is_authenticated():
        logger.debug("User authenticated, getting recommendations")
        recommended_films = recom_helper.get_best_psi_films_queryset(
            user_id = request.user.id,
            tags = tag,
            limit = 25, # TODO: customize
            offset = 0,
        )
    else:
        logger.debug("User not authenticated, skipping recommendations")

    from django.db.models import Q
    from film20.useractivity.models import UserActivity
    from film20.blog.models import Post

    select_query = 'SELECT DISTINCT "useractivity_useractivity".* '
    from_query = ' FROM "useractivity_useractivity" '
    join_query = ' LEFT OUTER JOIN "blog_post" ON ("useractivity_useractivity"."post_id" = "blog_post"."parent_id") LEFT OUTER JOIN "core_object" ON ("blog_post"."parent_id" = "core_object"."id") '
    where_query = ' WHERE "useractivity_useractivity"."LANG" = %(language_code)s  AND (("core_object"."status" = %(post_status)s  AND "useractivity_useractivity"."activity_type" = %(useractivity_type_post)s) OR "useractivity_useractivity"."activity_type" = %(useractivity_type_short_review)s  OR "useractivity_useractivity"."activity_type" = %(useractivity_type_comment)s ) '
    order_by = ' ORDER BY "useractivity_useractivity"."created_at" DESC '
    params = {'language_code': LANGUAGE_CODE, 'post_status': Post.PUBLIC_STATUS, 'useractivity_type_post': UserActivity.TYPE_POST, 'useractivity_type_short_review': UserActivity.TYPE_SHORT_REVIEW, 'useractivity_type_comment': UserActivity.TYPE_COMMENT}

    activities = {
        'select': select_query,
        'from' : from_query,
        'join' : join_query,
        'where': where_query,
        'order_by': order_by,
        'params': params
    }

    activities = recom_helper.enrich_query_with_tags(activities, tag, film_id_string="useractivity_useractivity.film_id" )
    query, params = recom_helper._perform_queries(activities)
    activities = UserActivity.objects.raw(query, params)
    activities = activities[:5]

    # TODO refactor together with same query from core/views/show_main
    select_query = 'SELECT DISTINCT "blog_post".* '
    from_query = ' FROM "blog_post" '
    join_query = ' INNER JOIN "core_object" ON ("blog_post"."parent_id" = "core_object"."id") INNER JOIN "blog_post_related_film" ON ("blog_post"."parent_id" = "blog_post_related_film"."post_id") INNER JOIN "auth_user" ON ("blog_post"."user_id" = "auth_user"."id") '
    where_query = ' WHERE "blog_post"."LANG" = %(language_code)s  AND "core_object"."status" = %(post_status)s  AND "blog_post_related_film"."film_id" IS NOT NULL AND "blog_post"."featured_note" = false  AND "blog_post"."is_published" = true  AND NOT ("blog_post"."featured_note" = true ) '
    order_by = ' ORDER BY "blog_post"."publish" DESC '
    featured_reviews = {
        'select': select_query,
        'from' : from_query,
        'join' : join_query,
        'where': where_query,
        'order_by': order_by,
        'params': params
    }

    featured_reviews = recom_helper.enrich_query_with_tags(featured_reviews, tag,  "blog_post_related_film.film_id")
    query, params = recom_helper._perform_queries(featured_reviews)
    featured_reviews = Post.objects.raw(query, params)
    featured_reviews = featured_reviews[:settings.NUMBER_OF_REVIEWS_TAG_PAGE]
    
    context = {
        'ranking': ranking,
        'recommendations': recommended_films,
        'page': 1,
        'tag': tag,
        'activities': activities,
        'featured_reviews': featured_reviews,
        'festival': festival,
    }


    return render_to_response(
		templates['SHOW_TAG_PAGE'],
        context, 
        context_instance = RequestContext(request))

def show_films_for_tag(request, tag=None, page_id = "1"):
    """
        Shows a sortable and pageable list of films for a tag
    """

    if tag == None:
        raise Http404

    recom_helper = RecomHelper()
    films_list = recom_helper.get_films_for_tag(tag = tag)

    logger.debug(films_list)

    paginate_by = 75
    paginator = Paginator(films_list, paginate_by)
    paginator._count = len(films_list)

    try:
        films = paginator.page(page_id)
    except (EmptyPage, InvalidPage):
        films = paginator.page(paginator.num_pages)        

    context = {
        'tag': tag,
        'films': films,
    }

    return render_to_response(templates['FILMS_FOR_TAG'],
            context,
            context_instance=RequestContext(request))
