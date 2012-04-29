import logging;
logger = logging.getLogger(__name__)

from film20.utils.test import TestCase
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.test.client import Client

from film20.core.models import Film, FilmRanking, Rating
from film20.core.rating_helper import BasketsRatingHelper
from film20.tagging.models import *
from film20.filmbasket.models import BasketItem


class RateFilmsTestCase(TestCase):
    fixtures = ['test_films.json']
    def setUp(self):
        logger.info("setting up few films")
        self.film_pos = {}
        for i in range(100):
            film = Film.objects.create(
                permalink="test-film-%d" % i,
                title="title %2d" % i,
                type=Film.TYPE_FILM,
                release_year=2000,
            )
            self.film_pos[film.id] = i+1
            FilmRanking.objects.create(
                    film=film,
                    average_score=str((99 - i) / 10.0),
                    number_of_votes=99-i,
                    type=1,
            )
        self.user = User.objects.create_user("test", "test@test.com", "testpasswd")
        self.client = Client()
        self.client.login(username='test', password='testpasswd')

    def test_get_user_seen_films(self):
        """ Tests storing rated and seen films in cache. """

        films = Film.objects.all()
        API_VERSION = "1.1"
        username = self.user.username
        put_url = "/api/" + API_VERSION + "/user/" + username + "/ratings/film/"

        # We rate movies and check if they were added to seen_films
        for film in films[:10]:
            film_put_url = put_url + film.permalink + "/" + str(Rating.TYPE_FILM) + "/"
            self.client.put(film_put_url, {'rating': 2})
            # We check if the film was added to user_seen_films
            seen_films = Film.get_user_seen_films(self.user)
            self.assertTrue(film.id in seen_films)

        # We mark movies as seen and check if they were added to seen_films
        for film in films[10:20]:
            film.mark_as_seen(self.user)
            # We check if the film was added to user_seen_films
            seen_films = Film.get_user_seen_films(self.user)
            self.assertTrue(film.id in seen_films)



    def test_rate_films2(self):

        TAGS_LIST = settings.BASKETS_TAGS_LIST
        settings.RATE_BASKET_SIZE = len(TAGS_LIST)
        API_VERSION = "1.1"
        username = self.user.username
        put_url = "/api/" + API_VERSION + "/user/" + username + "/ratings/film/"

        # tag films
        films = Film.objects.all()
        tag_index = 0
        tags_number = len(TAGS_LIST)
        # one film has all the tags
        for tag in TAGS_LIST:
            films[0].save_tags(tag)

        for film in films[1:]:
            film.save_tags(TAGS_LIST[tag_index])
            tag_index = (tag_index + 1) % tags_number

        seen_films = set()
        while True:
            films_to_rate = BasketsRatingHelper.get_films_to_rate(self.user, 6)
            if films_to_rate:
                for film in films_to_rate:
                    self.assertTrue(film not in seen_films)
                    # rate this film
                    film_put_url = put_url + film.permalink + "/" + str(Rating.TYPE_FILM) + "/"
                    self.client.put(film_put_url, {'rating': 10})

                seen_films.update(films_to_rate)
            else:
                break

    def test_rate_films(self):
        cache.set('test', True)
        self.assertTrue(cache.get('test'))
        
        cache.clear()
        self.assertTrue(cache.get('test') is None)

        settings.RATING_BASKET_SIZE = 20
        
        all_films = set()

        films = Film.get_films_to_rate(self.user, 20)
        all_films.update(f.id for f in films)
        logger.info("film ids: %r", [f.id for f in films])
        self.assertTrue(all(self.film_pos[f.id]<=20 for f in films))
        
        films[0].mark_as_seen(self.user)

        BasketItem.objects.create(film=films[1], wishlist=1,
                user=self.user)

        Rating.objects.create(type=1, film=films[2], rating=5, 
                parent=films[2], user=self.user)
      
        films = Film.get_films_to_rate(self.user, 17)
        for f in films:
            f.mark_as_seen(self.user)

        # second basket
        films = Film.get_films_to_rate(self.user, 10)
        all_films.update(f.id for f in films)
        logger.info("film ids: %r", [f.id for f in films])
        self.assertTrue(all(self.film_pos[f.id]>20 and self.film_pos[f.id]<=40 for f in films))
        for f in films:
            f.mark_as_seen(self.user)

        cache.clear()

        films = Film.get_films_to_rate(self.user, 10)
        all_films.update(f.id for f in films)
        self.assertTrue(all(self.film_pos[f.id]>20 and self.film_pos[f.id]<=40 for f in films))
        for f in films:
            f.mark_as_seen(self.user)

        films = Film.get_films_to_rate(self.user, 100)
        all_films.update(f.id for f in films)
        for f in films:
            f.mark_as_seen(self.user)
        self.assertEquals(len(films), 60)

        self.assertEquals(len(all_films), 100)

        self.assertFalse(Film.get_films_to_rate(self.user, 1))

    def test_rating_useractivity(self):
        from film20.useractivity.models import UserActivity
        from film20.core.models import UserRatingTimeRange
        from film20 import notification
        from film20.tagging.models import Tag, TaggedItem
        
        notification.models.test_queue = []

        film = Film.objects.get(permalink='pulp-fiction')
        film.save_tags('hamburger')

        film2 = Film.objects.get(permalink='the-godfather')

        Rating.objects.filter(user=self.user, film=film).delete()

        film.rate(self.user, 10)
        film2.rate(self.user, 8)
        
        self.assertFalse(UserActivity.objects.filter(user=self.user))

        UserRatingTimeRange.process_rating_timerange(0)

        activities = list(UserActivity.objects.filter(user=self.user))
        self.assertTrue(len(activities), 1)

        self.assertEquals(activities[0].activity_type, UserActivity.TYPE_RATING)
        self.assertEquals(activities[0].content, "1") # one extra film rated

        self.assertTrue(notification.models.test_queue)

        self.assertTrue(TaggedItem.objects.get_by_model(UserActivity, 'hamburger'))

        self.assertTrue('hamburger' in [str(t) for t in Tag.objects.get_for_object(activities[0])])

