# Django
from django.core.management.base import BaseCommand, CommandError

# Project
from film20.import_films.imdb_fetcher import get_movie_by_id, get_movie_by_title_and_year
from film20.core.models import Film

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def verify_imdb_codes(self):
        films = Film.objects.all().order_by('imdb_code')

        none = []
        alt = []

        for film in films:
            logger.info("Movie %s" %film)
            if not film.imdb_code:
                film.verified_imdb_code = False
                logger.error("Movie %s have no IMDB code" % film)
                movie = {"film_id":film.id, "film_title":film.title, "imdb_code":"missing_imdb_code", "imdb_akas":None}
                none.append(movie)

            else:
                movie = get_movie_by_id(film.imdb_code, "http")
                logger.info("Get movie by IMDB id %s", film.imdb_code)

                if movie:
                    year = movie.get('year')
                    title = movie.get('title')
                    akas = movie.get('akas')

                    if year:
                        if title == film.title:
                            film.verified_imdb_code = True
                            film.release_year = year
                            logger.info("Matched title %s" % film)
                        else:
                            found = False
                            for aka in akas:
                                title = aka.split('::')[0]
                                logger.info("Check alternative title %s for %s" % (title, film.title))
                                if title == film.title:
                                    film.verified_imdb_code = False
                                    film.release_year = year
                                    film.title = title
                                    logger.info("Found movie %s by alternative title" % film)
                                    movie = {"film_id":film.id, "film_title":film.title, "imdb_code":film.imdb_code,  "imdb_title":movie.get('title'), "imdb_akas":akas}
                                    alt.append(movie)
                                    found = True
                            if not found:
                                film.verified_imdb_code = False
                                logger.error("Missing title for %s in IMDB" % film)
                                movie = {"film_id":film.id, "film_title":film.title, "imdb_code":film.imdb_code, "imdb_akas":akas}
                                none.append(movie)
                    else:
                        film.verified_imdb_code = False
                        logger.error("Wrong year: %s (%s), should be %s" %(film, film.release_year, year))
                        movie = {"film_id":film.id, "film_title":film.title, "imdb_code":film.imdb_code, "imdb_akas":akas}
                        none.append(movie)

                else:
                    film.verified_imdb_code = False
                    logger.error("Movie %s not found" % film)
                    movie = {"film_id":film.id, "film_title":film.title, "imdb_code":film.imdb_code, "imdb_akas":"missing_imdb_film"}
                    none.append(movie)
            film.save()
        return alt, none

    def handle(self, *args, **opts):
        alt, none = self.verify_imdb_codes()
        print "---------- ALT -------------"
        print len(alt)
        print alt
        print "---------- NONE -------------"
        print len(none)
        print none
