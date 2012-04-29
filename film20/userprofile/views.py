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
# coding=utf-8
# Python
import logging

# Django
from django.http import Http404
from django.views.generic.list import ListView
from film20.recommendations.views import FilterSpecsForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404

# Project
from film20.config import urls
from film20.recommendations.views import specs_form
from film20.recommendations.forms import get_rating_type_as_int, get_rating_types_to_display
from film20.recommendations.recom_helper import RecomHelper
from film20.core import rating_helper
from film20.filmbasket.models import BasketItem
from film20.useractivity.models import UserActivity
from django.conf import settings

logger = logging.getLogger(__name__)

# -- Unified Views for Dashboard and PublicProfile -- #

from film20.core.views import PaginatorListView, UsernameMixin

from film20.useractivity.views import WallView

class ArticlesListView(UsernameMixin, WallView):
    page_size = 10
    list_of_pages = True
#    context_object_name = 'activities'
    draft = False

    def get_draft_or_published(self):
        the_key = _('drafts')
        params = self.request.GET.copy()
        if the_key in params:
            self.draft = True

    def get_context_data(self, **kwargs):
        context = super(ArticlesListView, self).get_context_data(**kwargs)
        context['drafts'] = self.draft
        return context

    def get_queryset(self):
        self.get_username()
        self.get_draft_or_published()
        if self.draft:
            articles = UserActivity.objects.draft_articles_for_user(self.user)
        else:
            articles = UserActivity.objects.articles_for_user(self.user)
        return articles

class FollowedListView(UsernameMixin, PaginatorListView):
    """ Users followed by given user."""
    page_size = getattr(settings, "FOLLOWED_USERS_FOR_PAGE", 20)
    show_all = True
    list_of_pages = True
    context_object_name = 'users'

    def get_context_data(self, **kwargs):
        context = super(FollowedListView, self).get_context_data(**kwargs)
        context['followed_number'] = self.user.followers.following().count()
        return context

    def get_queryset(self):
        self.get_username()
        following = self.user.followers.following()
        return following

class FollowersListView(UsernameMixin, PaginatorListView):
    """ Users that follow given user."""
    page_size = getattr(settings, "FOLLOWED_USERS_FOR_PAGE", 20)
    show_all = True
    list_of_pages = True
    context_object_name = 'users'

    def get_context_data(self, **kwargs):
        context = super(FollowersListView, self).get_context_data(**kwargs)
        context['followers_number'] = self.user.followers.followers().count()
        return context

    def get_queryset(self):
        self.get_username()
        followers = self.user.followers.followers()
        return followers

class SimilarUsersListView(UsernameMixin, PaginatorListView):
    """ Users that are similar to given user."""
    page_size = getattr(settings, "NUMBER_OF_SIMILAR_USERS_ON_PAGE", 22)
    page_count = getattr(settings, "NUMBER_OF_SIMILAR_USERS_PAGES", 10)
    filmaster_type = 'all'
    users_limit = page_size * page_count
    show_all = True
    list_of_pages = True
    context_object_name = 'users'


    def get_context_data(self, **kwargs):
        context = super(SimilarUsersListView, self).get_context_data(**kwargs)
        context['similar_users_limit'] = self.users_limit
        context['filmaster_type'] = self.filmaster_type
        context['user_checked'] = self.user
        return context

    def get_queryset(self):
        self.get_username()
        recom_helper = RecomHelper()
        users = recom_helper.get_best_tci_users(user=self.user, limit=self.users_limit, filmaster_type= self.filmaster_type)
        return users

class SimilarUsersFollowingListView(SimilarUsersListView):
    """ Followers of given users that are similar to him """
    filmaster_type = 'following'

class SimilarUsersFollowedListView(SimilarUsersListView):
    """ User that the given given user follows that are similar to him """
    filmaster_type = 'followed'

class CollectionListView(UsernameMixin, PaginatorListView):
    page_size = 20
    show_all = True
    list_of_pages = True

    def get_filmbasket_type(self, **kwargs):
        kind = self.kwargs['kind']
        if kind == urls.urls["OWNED"]:
            type = "OWNED"
        elif kind == urls.urls["WISHLIST"]:
            type = BasketItem.DYING_FOR
        elif kind == urls.urls["SHITLIST"]:
            type = BasketItem.NOT_INTERESTED
        else:
            raise Http404
        return type

    def get_context_data(self, **kwargs):
        context = super(CollectionListView, self).get_context_data(**kwargs)

        type = self.get_filmbasket_type()
        context['type'] = type
        context['collection_view'] = True
        return context

    def get_queryset(self):
        self.get_username()
        type = self.get_filmbasket_type()
        logger.debug("Film Basket: " + unicode(type))

        if type == "OWNED":
            films = BasketItem.objects.filter(user=self.user,
                    owned=BasketItem.OWNED)
        else:
            films = BasketItem.objects.filter(user=self.user, wishlist=type)
        return films

class RatingsListView(UsernameMixin, PaginatorListView, FilterSpecsForm):
    page_size = 20
    list_of_pages = True
    show_all = True

    def get_type(self, **kwargs):
        if 'type_as_str' in self.kwargs:
            self.type_as_str = get_rating_type_as_int(self.kwargs['type_as_str'])
        else:
            self.type_as_str = get_rating_type_as_int('film')
        if self.type_as_str == None:
            raise Http404

    def get_sort_by(self):
        sort_key = 'sort_by'
        params = self.request.GET.copy()
        self.sort_by = '-rating'
        if sort_key in params:
            if params[sort_key] == 'title':
                self.sort_by = 'film__title'
            elif params[sort_key] == 'asc':
                self.sort_by = 'rating'
            elif params[sort_key] == 'date':
                self.sort_by = '-last_rated'

    def get_context_data(self, **kwargs):
        context = super(RatingsListView, self).get_context_data(**kwargs)

        recom_helper = RecomHelper()

        context['ratings_user'] = self.user
        context['rating_type_str'] = rating_helper.get_rating_type_label(self.type_as_str)
        context['type_as_str'] = self.type_as_str
        context['rating_types'] = get_rating_types_to_display()
        context['ratings_count'] = recom_helper.count_ratings(user_id = self.user.id)
        context['ratings_for_user_id'] = self.user.id
        return context

    def get_queryset(self):
        is_valid, fake_film_specs_form, film_specs_form = self.get_specs_form()
        self.get_username()
        self.get_type()
        self.get_params()
        self.get_sort_by()

        tags = None
        year_from = None
        year_to = None
        related_director = None
        related_actor = None
        popularity = None
        if is_valid:
            tags = fake_film_specs_form.tags
            year_from = fake_film_specs_form.year_from
            year_to = fake_film_specs_form.year_to
            related_director = fake_film_specs_form.related_director_as_object
            related_actor = fake_film_specs_form.related_actor_as_object
            popularity = fake_film_specs_form.popularity

        recom_helper = RecomHelper()
        ratings = recom_helper.get_all_ratings(
            user_id = self.user.id,
            type = self.type_as_str,
            tags = tags,
            year_from = year_from,
            year_to = year_to,
            related_director = related_director,
            related_actor = related_actor,
            order_by=self.sort_by
        )
        #logger.debug(ratings)
        return ratings
