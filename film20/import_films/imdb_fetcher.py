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

import os, sys, glob, re
import imdb, imdb.helpers, pickle
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError
try:
    from PIL import Image
except ImportError:
    import Image
from django.db import models, transaction, IntegrityError
from django.contrib.auth.models import User
from django.contrib import admin
from django.core.files import File

from film20.utils import slughifi
from film20.settings import *
from film20.core.models import *
from film20.tagging.models import Tag
from film20.import_films.models import *
from film20.utils.posters import is_image_valid

import logging
logger = logging.getLogger(__name__)

try:
    from film20.notification import models as notification
except ImportError:
    notification = None

NUMBER_OF_ATTEMPTS = getattr(settings, "NUMBER_OF_ATTEMPTS", 3)

logging.basicConfig(level=logging.DEBUG, filename='fetch.log', filemode='w')
#logging.basicConfig(level=logging.DEBUG)

def unescape_imdb_text(imdb_text):
    #imdb_text = imdb_text.encode('utf-8', 'xmlcharrefreplace')
    p = re.compile('&#(\d*);')
    p2 = re.compile('&#x([\da-fA-F]{2});')
    text = p.sub(lambda entity: unichr(int(entity.group(1))), imdb_text)             
    return p2.sub(lambda entity: unichr(int(entity.group(1), 16)), text)    
    #return imdb_text
    
def unescape_imdb_texts_in_db(): 
    reg = r'.*&#(x[a-fA-F\d]{2})|(\d{4})*;.*'
    list = Film.objects.filter(title__regex=reg)
    for f in list:
        f.title = unescape_imdb_text(f.title)
        f.save()
    if list:
        print 'unescaped %i films' % len(list)
    list = FilmLocalized.objects.filter(title__regex=reg)
    for f in list:
        f.title = unescape_imdb_text(f.title)
        f.save()
    if list:
        print 'unescaped %i localized films' % len(list)
        
    list = Person.objects.filter(Q(name__regex=reg) | Q(surname__regex=reg))
    for p in list:
        p.name = unescape_imdb_text(p.name)
        p.surname = unescape_imdb_text(p.surname)
        p.save()
    if list:
        print 'unescaped %i people' % len(list)        
    list = PersonLocalized.objects.filter(Q(name__regex=reg) | Q(surname__regex=reg))
    for p in list:
        p.name = unescape_imdb_text(p.name)
        p.surname = unescape_imdb_text(p.surname)
        p.save()
    if list:
        print 'unescaped %i localized people' % len(list)
        
    
def save_last_imdbid(imdbID):
    imdbID = str(imdbID)
    file = open('last_imdbid.txt', 'w')
    file.write(imdbID)
    file.close()

def get_movie_list(MOVIE_LIST_FILE):
    file = open(MOVIE_LIST_FILE)
    movie_list = file.read()
    movies = movie_list.split('\n')
    return movies

def get_ids(IDS_LIST_FILE):
    file = open(IDS_LIST_FILE)
    ids_list = file.read()
    imdbids = ids_list.split('\n')
    return imdbids

def pickle_movie(movie):
    movie_title = unescape_imdb_text(movie.get('title'))
    filename = slughifi.slughifi(movie_title)
    filepath = MOVIE_DIRECTORY + filename + '.pickle'
    f = open(filepath, 'w')
    pickle.dump(movie, f)

def get_movie_by_title_and_year(title, year):
    IMDB = imdb.IMDb()
    IMDB.do_adult_search(0)
    results = IMDB.search_movie(title)

    # fix for wrong title parsing
    for movie in results:
        if movie.get( 'year' ) is None:
            pattern = re.compile( '(?P<title>.*)\(.* (?P<year>\d{4})\).*', re.DOTALL )
            m = re.match( pattern, movie.get( 'title' ) )
            if m is not None:
                movie['year'] = int( m.group( 'year' ) )
                movie['title'] = m.group( 'title' ).strip()

    results  = [movie for movie in results if movie['kind'] == "movie" or movie['kind'] == 'video movie' or movie['kind'] == 'tv movie' or movie['kind'] == 'tv mini series'or movie['kind'] == 'tv mini-series'or movie['kind'] == 'tv']
    exact = [f for f in results if unescape_imdb_text(f['title'])==title and f['year']==year]
    if exact:
        if len(exact)>1:
            print "WARN: search for %s (%s) yielded multiple results: %s" % (title, year, exact)
        return exact[0]
    return None

def get_movie_by_title(title, conntype, auto=None):
    if conntype=="http":
        a = imdb.IMDb()
    else:
        a = imdb.IMDb('sql',DATABASE_URI)
    a.do_adult_search(0)
    list = a.search_movie(title)
    movie = list[0]
    if auto==False:
        a.update(movie, 'main')
        return movie
    if auto==True:
        if movie['kind'] == "movie":
            a.update(movie, 'main')
            return movie            

from film20.utils.texts import levenshtein
def match_director(movie, director, distance=0):
    for d in movie.get('director', ()):
        if levenshtein(director, d.get('name', ''))<=distance:
	    return True

def match_directors(movie, directors, distance=0):
    return any(match_director(movie, d, distance) for d in directors)

def get_movies_by_title_and_directors(title, directors, distance=0):
    db = imdb.IMDb()
    db.do_adult_search(0)
    movies = [m for m in db.search_movie(title) if m.get('kind') == 'movie']
    for movie in movies:
        db.update(movie, 'main')
    return [m for m in movies if match_directors(m, directors, distance)]

def get_movie_by_id(imdbID, conntype):
    #imdbID = int(imdbID)
    if conntype=="http":
        a = imdb.IMDb()
    else:
        a = imdb.IMDb('sql',DATABASE_URI)
    a.do_adult_search(0)
    movie = a.get_movie(imdbID)
    kind = None
    kind = movie['kind']
    if movie is None:
        return False
    if kind:
        if movie['kind'] == "movie" or movie['kind'] == 'video movie' or movie['kind'] == 'tv movie' or movie['kind'] == 'tv mini series'or movie['kind'] == 'tv mini-series'or movie['kind'] == 'tv':
            return movie
        else:
            return False
    else:
        return False

def unpickle_movie(path):
    #last_imdbid = get_last_imdbid(LAST_IMDBID_FILE)
    for filename in glob.iglob( os.path.join(path, '*.pickle') ):
        f = open(filename, 'r')
        movie = pickle.load(f)
        save_movie_to_db(movie)

def save_directors(directors, film):
    for director in directors:
        name_surname = unescape_imdb_text(director.get('name'))
        director_link = slughifi.slughifi(name_surname)
        director_imdb = director.personID
        director_name, director_surname = save_name_surname(name_surname)
        if len(director_name) > 50:
            director_name = director_name[0:50]
        if len(director_surname) > 50:
            director_surname = director_surname[0:50]    
        dbdir = Person.objects.filter(permalink = director_link)
        if dbdir.count() == 0:
            try:
                person = Person.objects.get(imdb_code=director_imdb, verified_imdb_code=False)
                person.imdb_code=None
                person.save()
            except Person.DoesNotExist:
                pass
            person = Person(name = director_name, surname = director_surname, is_director = True, status = 1,
                            version = 1, type=2, permalink = director_link, imdb_code =director_imdb,
                            actor_popularity=0,director_popularity=0,actor_popularity_month=0,
                            director_popularity_month=0,writer_popularity=0,writer_popularity_month=0,
                            verified_imdb_code=True)
            person.save(saved_by=2)
            film.directors.add(person)
        else:
            person = dbdir[0]
            person.is_director = True                    
            person.save(saved_by=2)
            film.directors.add(person)
    logger.debug("Saved directors for film: " + unicode(film.title))

def save_name_surname(name_surname):
    PREFIXES = {
        'ab':'ab',
        'Ab':'Ab',
        'abu':'abu',
        'Abu':'Abu',
        'bin':'bin',
        'Bin':'Bin',
        'bint':'bint',
        'Bint':'Bint',
        'da':'da',
        'Da':'Da',
        'de':'de',
        'De':'De',
        'degli':'degli',
        'Degli':'Degli',
        'della':'della',
        'Della':'Della',
        'der':'der',        
        'Der':'Der',
        'di':'di',
        'Di':'Di',
        'del':'del',
        'Del':'Del',
        'dos':'dos',
        'Dos':'Dos',
        'du':'du',
        'Du':'Du',
        'el':'el',
        'El':'El',
        'fitz':'fitz',
        'Fitz':'Fitz',
        'haj':'haj',
        'Haj':'Haj',
        'hadj':'hadj',
        'Hadj':'Hadj',
        'hajj':'hajj',
        'Hajj':'Hajj',
        'ibn':'ibn',
        'Ibn':'Ibn',
        'ter':'ter',
        'Ter':'Ter',
        'tre':'tre',
        'Tre':'Tre',
        'van':'van',
        'Van':'Van',
        'Von':'Von',
        'von':'von',
        }
    
    list = name_surname.split(' ')
    if len(list)> 2:
        for index, element in enumerate(list):
            if PREFIXES.has_key(element):
                name = " ".join(list[:index])
                surname = " ".join(list[index:])
                return [name, surname]
            elif list[-1] == "Jr.":
                name = " ".join(list[:-2])
                surname = " ".join(list[-2:])
                return [name, surname]
            else:    
                name = list[0]
                surname = " ".join(list[1:])
                return [name, surname]
    elif len(list) ==  2:
        name = list[0]
        surname = list[1]
        return [name, surname]
    else:
        name = list[0]
        surname = list[0]
        return [name, surname]
            
def save_actors(actors, film):
    for index, actor in enumerate(actors):
        name_surname = unescape_imdb_text(actor.get('name'))
        actor_imdb = actor.personID
        character_name = unescape_imdb_text(unicode(actor.currentRole))
        if len(character_name) > 255:
            character_name = character_name[0:254]
        importance_ind = index
        actor_link = slughifi.slughifi(name_surname)
        actor_name, actor_surname = save_name_surname(name_surname)
        if len(actor_name) > 50:
            actor_name = actor_name[0:50]
        if len(actor_surname) > 50:
            actor_surname = actor_surname[0:50]    
        dbdir = Person.objects.filter(permalink = actor_link)
        if dbdir.count() == 0:
            try:
                person = Person.objects.get(imdb_code=actor_imdb, verified_imdb_code=False)
                person.imdb_code=None
                person.save()
            except Person.DoesNotExist:
                pass
            person = Person(name = actor_name,
                            surname = actor_surname,
                            is_actor = True, version =1, type=2,
                            permalink = actor_link, status = 1,
                            actor_popularity=0,imdb_code = actor_imdb,
                            director_popularity=0,actor_popularity_month=0,
                            director_popularity_month=0,writer_popularity=0,writer_popularity_month=0,
                            verified_imdb_code=True)

            person.save(saved_by=2)
            character = Character(film=film, person=person, importance=importance_ind, character=character_name, LANG='en')
            character.save()
            # TODO: apply mapping for common character names
            character_pl = Character(film=film, person=person, importance=importance_ind, character=character_name, LANG='pl')
            character_pl.save()
        else:
            person = dbdir[0]
            person.is_actor = True
            person.save(saved_by=2)
            character = Character(film=film, person=person, importance=importance_ind, character=character_name, LANG='en')
            character.save()
            # TODO: apply mapping for common character names
            character_pl = Character(film=film, person=person, importance=importance_ind, character=character_name, LANG='pl')
            character_pl.save()
    logger.debug("Saved actors for film: " + unicode(film.title))

def save_writers(film, writers):
    for writer in writers:
        name_surname = unescape_imdb_text(writer.get('name'))
        writer_link = slughifi.slughifi(name_surname)
        writer_imdb = writer.personID
        writer_name, writer_surname = save_name_surname(name_surname)
        dbdir = Person.objects.filter(permalink = writer_link)
        if len(writer_name) > 50:
            writer_name = writer_name[0:50]
        if len(writer_surname) > 50:
            writer_surname = writer_surname[0:50] 
        if dbdir.count() == 0:
            try:
                person = Person.objects.get(imdb_code=writer_imdb, verified_imdb_code=False)
                person.imdb_code=None
                person.save()
            except Person.DoesNotExist:
                pass
            person = Person(name = writer_name, surname = writer_surname, is_writer = True,
                            status = 1, version = 1, type=2, permalink = writer_link,
                            imdb_code =writer_imdb, actor_popularity=0,director_popularity=0,
                            actor_popularity_month=0,director_popularity_month=0,
                            writer_popularity=0,writer_popularity_month=0,
                            verified_imdb_code=True)
            person.save(saved_by=2)
            film.writers.add(person)
            logger.debug("Saving Writer. ID=" + unicode(person))
        else:
            person = dbdir[0]
            person.is_writer = True                    
            person.save(saved_by=2)
            film.writers.add(person)
            logger.debug("Saving Writer. ID=" + unicode(person))
    logger.debug("Saved writers for film: " + unicode(film.title))


    
def save_countries(countries, film):
    for country in countries:
        list = country.split("::")
        if len(list) == 3:
            localized_title = unescape_imdb_text(list[0])
            country_code = list[2].strip("[").strip("]")
            if len(localized_title) > 128:
                localized_title = localized_title[0:127]
            film.save_localized_title(localized_title, country_code, saved_by=2)

def save_en_titles(countries, film):
    for country in countries:
        if needle_in_haystack("USA", country) or needle_in_haystack("English", country):
            if not needle_in_haystack("working title", country):
                list = country.split("::")
                title = list[0]
                if len(title) > 128:
                    title = title[0:127]
                film.save_localized_title(title, "en", saved_by=2)
    
def translate_tags(tags):
    tags_pl = ''
    
    dict = {
            'Action':'film akcji',
            'Adventure':'przygodowy',
            'Animation':'animowany',
            'Biography':'biograficzny',
            'Comedy':'komedia',
            'Crime':'sensacyjny',
            'Drama':'dramat',
            'Fantasy':'fantastyczny',
            'Film-Noir':'noir',
            'History':'historyczny',
            'Horror':'horror',
            'Music':'muzyczny',
            'Musical':'musical',
            'Mystery':'tajemnica',
            'Romance':'romans',
            'Sci-Fi':'science-fiction',
            'Sport':'sportowy',
            'Thriller':'dreszczowiec',
            'War':'wojenny',
            'Western':'western',
            'Short':'krotkometrazowy',
            'Sport':'sportowy',
            'Independent':'kino niezależne',
            'Family':'familijny',
            'Documentary':'dokumentalny',
    }
    
    for tag in tags:
        if dict.has_key(tag):
            tags_pl = dict[tag]+ ',' + tags_pl
        else:
            pass
    return tags_pl

def save_country_list(film, countries):
    for country in countries:
        country = unescape_imdb_text(country)
        country_list = Country.objects.filter(country=country)
        if country_list.count() == 0:
            coun = Country(country=country)
            coun.save()
            film.production_country.add(coun)
            logger.debug("Saving Country. ID=" + unicode(coun)) 
        else:
            coun = country_list[0]
            film.production_country.add(coun)
            logger.debug("Saving Country. ID=" + unicode(coun))    
    film.production_country_list = ",".join( countries )
    film.save()
    logger.debug("Saving CountryList. ID=" + unicode(film.production_country_list))

def fetch_poster(url):
    logger.debug("fetching: %r", url)
    try:
        htmlSource=urllib2.urlopen(url)
        poster = htmlSource.read()
        htmlSource.close()
    
        tmpfile = open("tmp.jpg", "wb")
        tmpfile.write(poster)
        tmpfile.close()

        if not is_image_valid("tmp.jpg"):
            logger.warning("invalid image")
            return False

        return True
    except Exception, e:
        logger.debug("Poster fetch error!" + unicode(e))
        return False
    
def resize_image():
    im1 = Image.open("tmp.jpg")
    im2 = im1.resize((71, 102), Image.ANTIALIAS)
    im2.save("tmp.jpg")
    
def save_poster(imdbobject, url):
    if fetch_poster(url):
        # we don't want to resize poster now!
        #resize_image()
        filename = str(imdbobject.permalink) + ".jpg"
        #filename = "1.jpg"
        if len(filename) > 80:
            filename = filename[:80]
        ia = len(filename)
        filenamelenght = str(ia)
        f = open('tmp.jpg', 'rb')
        myfile = File(f)
        imdbobject.hires_image.save(filename, myfile, save=False)
        return True
    else:
        return False


def get_localized_titles(country):
    list = country.split("::")
    if len(list) == 3:
        localized_title = list[0]
        contry_code = list[2].strip("[").strip("]")
        return localized_title, contry_code

def save_movie(movie, movie_link):
    movie_title = unescape_imdb_text(movie.get('title'))
    try:
        film = Film.objects.get(imdb_code=movie.movieID)
        logger.error("film %r with imdb_code %s is in db already", movie_title, movie.movieID)
        return film
    except Film.DoesNotExist:
        pass

    films = Film.objects.filter(permalink = movie_link)
    counter = 0
    for film in films:
        counter += 1

    if counter:
        movie_link = movie_link + "-" + str(counter)

    if len(movie_title)>128:
        movie_title_old = movie_title
        movie_title = movie_title_old[0:123] + "..."
        print "Truncating movie title from " + movie_title_old + " to " + movie_title
    movie_release_year = movie.get('year')
    if movie_release_year is None:
        movie_release_year = 0000
    movie_imdb = movie.movieID
    film = Film(title=movie_title, release_year=movie_release_year, version = 1, type=1, permalink=movie_link, status=1, imdb_code=movie_imdb, popularity=0, popularity_month=0)
    film.production_country_list = ""
    film.save(saved_by=2)

    tags_en = ''
    tags_pl = ''
        
    tags = movie.get('genre')
    if tags:
        tags_en = ','.join(tags)
        tags_en = tags_en.lower()
        tags_pl = translate_tags(tags)

    countries = movie.get('akas')
    if countries:
        save_countries(countries, film)
        
    production_countries = movie.get('countries')
    if production_countries:
        save_country_list(film, production_countries)        
    if tags_en:
        film.save_tags(tags_en, LANG="en", saved_by=2)
        
    if tags_pl:        
        film.save_tags(tags_pl, LANG="pl", saved_by=2)        

    directors = movie.get('director')
    if directors:
        save_directors(directors, film)
        
    actors = movie.get('actors')
    if actors:
        save_actors(actors, film)

    #logger.debug("Saved writers for film: " + unicode(film.title))
    writers = movie.get('writer')        
    if writers:
        save_writers(film, writers)

    save_film_poster(film, movie)

    logger.debug("Saved film: " + unicode(film.title))
    return film

def save_film_poster(film, imdb_movie=None):
    if not film.imdb_code:
        logger.warning("no imdb_code for %r", film)
        return False
    if not imdb_movie:
        try:
            imdb_movie = get_movie_by_id(film.imdb_code, 'http')
        except Exception, e:
            logger.warning("can't fetch imdb movie for %r: %s", film, unicode(e))
            return False
    ret = save_tmdb_poster(film) or \
        save_hires_imdb_poster(imdb_movie, film) or \
        save_imdb_poster(imdb_movie, film)
    if not ret:
        logger.warning("no poster available for %r", film)
        if film.tmdb_import_status != Film.IMPORT_FAILED_NO_POSTER:
            film.tmdb_import_status = Film.IMPORT_FAILED_NO_POSTER
            film.save()
    return ret

def save_imdb_poster(imdb_movie, film):
    try:
        url = imdb_movie.get('cover url')
        if not url:
            logger.debug("no lowres poster available for %r", film)
            return False
        if save_poster(film, url):
            film.tmdb_import_status = Film.IMPORTED_IMDB_LOWRES
            film.save()
            logger.debug("imdb lowres poster saved: %r", film.hires_image)
            return True
    except Exception, e:
        logger.warning(unicode(e))
    return False

def save_hires_imdb_poster(imdb_movie, film):
    try:
        url = imdb.helpers.fullSizeCoverURL(imdb_movie)
        if not url:
            logger.debug("no hires imdb poster available for %r", film)
            return False
        if save_poster(film, url):
            film.tmdb_import_status = Film.IMPORTED_IMDB
            film.save()
            logger.debug("imdb hires poster saved: %r", film.hires_image)
            return True
    except Exception, e:
        logger.warning(unicode(e))
        return False

def save_tmdb_poster(film):
    try:
        from film20.import_films.tmdb_poster_fetcher import fetch_film_by_title, save_tmdb_poster as _save_tmdb_poster
        tmdb_film = fetch_film_by_title(film)
        if tmdb_film and _save_tmdb_poster(film, tmdb_film):
            film.tmdb_import_status = Film.IMPORTED_TMDB
            film.save()
            logger.debug("tmdb hires poster saved: %r", film.hires_image)
            return True
    except Exception, e:
        logger.warning(unicode(e))
    return False

@transaction.commit_on_success
def save_movie_to_db(movie):
    movie_title = unescape_imdb_text(movie.get('title'))
    if len(movie_title)>128:
        movie_title_old = movie_title
        movie_title = movie_title_old[0:123] + "..."
    #yy = movie.get('year')
    movie_link = slughifi.slughifi(movie_title)

    films = Film.objects.filter(title__iexact = movie_title)
    status = None
    if films.count() > 0:
        for film in films:
            movie_link = movie_link + "-" + str(movie.get('year'))
            try:
                film = Film.objects.get(title__iexact = movie_title, release_year=movie.get('year'), imdb_code = movie.movieID)
                logger.warning("movie %r - %r already in db", movie_title, movie.get('year'))
                if not film.imdb_code:
                    film.imdb_code = movie.movieID
                    film.save()
                status = FilmToImport.ALREADY_IN_DB
                return film, status
            except Film.DoesNotExist:
                saved_film = save_movie(movie, movie_link)
                status = FilmToImport.ACCEPTED
                return saved_film, status
            except Exception, e:
                logger.exception(e)
                return False, status
    else:
        try:
            film = Film.objects.get(permalink=movie_link)
            movie_link = movie_link + "-" + str(movie.get('year'))
            saved_film = save_movie(movie, movie_link)
            status = FilmToImport.ALREADY_IN_DB
            return saved_film, status
        except Film.DoesNotExist:
            saved_film = save_movie(movie, movie_link)
            status = FilmToImport.ACCEPTED
            return saved_film, status
        
def return_release_day(release_dates):
    if release_dates:
#        print release_dates[0]
        pom = release_dates[0]
        pom2 = pom.split('::')
        print pom2[1]
#        pom3 = pom2[1]
#        dates = pom3.split(' ')
#        month_name = dates[1]
#        month_numbers = {"January" : "01", "February" : "02", "March" : "03", "April" : "04", "May" : "05", "June" : "06", "July" : "07", "August" : "08", "September" : "09", "October" : "10",  "November" : "11", "December" : "12"}
#        month = month_numbers[month_name]
#        import datetime
#        iday = int(dates[0])
#        iyear = int(dates[2])
#        imonth = int(month)
#        release_day = datetime.datetime(iyear, imonth, iday)
#        return release_day
#    else:
#        release_day = datetime.datetime(0, 0, 0)
#        return release_day

def imdb_movie_to_film( movie ):
    movie_title = unescape_imdb_text( movie.get( 'title' ) )
    if len( movie_title ) > 128:
        movie_title = movie_title[0:123] + "..."

    movie_link = slughifi.slughifi( movie_title )

    films = Film.objects.filter( title__iexact = movie_title )
    if films.count() > 0:
        for film in films:
            movie_link = movie_link + "-" + str( movie.get( 'year' ) )
            try:
                return Film.objects.get( title__iexact = movie_title, release_year = movie.get( 'year' ), imdb_code = movie.movieID )
            except Film.DoesNotExist:
                pass
    else:
        try:
            return Film.objects.get( permalink = movie_link )
        except Film.DoesNotExist:
            pass

def send_import_fail_notification( film_to_import, imdb_movie = None ):
    if notification:
        if film_to_import.status == FilmToImport.ALREADY_IN_DB:
            film = imdb_movie_to_film( imdb_movie )
        else:
            film = None

        args = {
            "film_to_import": film_to_import,
            "film": film
        }

        notification.send( [ film_to_import.user ], "film_import_failed", args )

def run(pickle, unpickle, list, single_movie, idlist, cron_job, conntype, single_movie_title = ''):
    
    if unpickle:
        unpickle_movie(MOVIE_DIRECTORY)
    
    if list and pickle:
        movie_list = get_movie_list(MOVIE_LIST_FILE)
        for title in movie_list:
            movie = get_movie_by_title(title, conntype)
            save_movie_to_db(movie)
            pickle_movie(movie)
            
    if list:
        movie_list = get_movie_list(MOVIE_LIST_FILE)
        for title in movie_list:
            if title != "":
                movie = get_movie_by_title(title, conntype, auto=True)
                if movie:
                    save_movie_to_db(movie)
            else:
                sys.exit()
            
    if single_movie:
        movie = get_movie_by_title(single_movie_title, conntype, auto=False)
        if movie:
            save_movie_to_db(movie)
    
    if single_movie and pickle:
        movie = get_movie_by_title(single_movie_title, conntype)
        if movie:
            save_movie_to_db(movie)
            pickle_movie(movie)
    
    if idlist:
        imdbids = get_ids(IDS_LIST_FILE)
        for imdbid in imdbids:
            if imdbid != "":
                movie = get_movie_by_id(imdbid, conntype)
                if movie:
                    save_movie_to_db(movie)
            else:
                sys.exit()
    
    if cron_job:
        films_to_import = FilmToImport.objects.filter(imdb_id__isnull=False, is_imported=False, status=FilmToImport.ACCEPTED, \
                                                      attempts__lt = NUMBER_OF_ATTEMPTS)
        for film_to_import in films_to_import:
            try:
                movie = get_movie_by_id(film_to_import.imdb_id, conntype)
                if movie:
                    saved_movie, status = save_movie_to_db(movie)
                    if status == FilmToImport.ACCEPTED:
                        if saved_movie:
                            film_to_import.is_imported = True
                            film_to_import.status = 1
                            film_to_import.attempts = film_to_import.attempts + 1
                            film_to_import.save()
                            importedfilm = ImportedFilm(user=film_to_import.user, film=saved_movie)
                            importedfilm.save()

                            if notification:
                                notification.send( [ importedfilm.user ], "film_imported", { "film": importedfilm } )

                            print "Imported: " + unicode(film_to_import.title) + "(" + unicode(film_to_import.imdb_url) + ")"
                    else:
                        film_to_import.status = 3
                        film_to_import.attempts = film_to_import.attempts + 1
                        film_to_import.save()
                        
                        send_import_fail_notification( film_to_import, movie )
                else:
                    film_to_import.attempts = film_to_import.attempts + 1
                    film_to_import.status = 4
                    film_to_import.save()

                    send_import_fail_notification( film_to_import )

            except Exception, e:
                import sys, traceback
                traceback.print_exc(file=sys.stdout)
                try:
                    e.print_stack_trace()
                except Exception, e1:
                    print "exception when printing stack trace!"

                try:
                    print(e)
                    print "FAILED to import: " + unicode(film_to_import.title) + "(" + unicode(film_to_import.imdb_url) + ")"
                except Exception, e:
                    print "FAILED to import movie with IMDB code: " + unicode(film_to_import.imdb_url)
                    print "Exception occured when exception handling:"
                    print(e)

                film_to_import.attempts = film_to_import.attempts + 1
                film_to_import.save()
                
                if film_to_import.attempts > NUMBER_OF_ATTEMPTS:
                    film_to_import.status = 2
                    film_to_import.save()

                    send_import_fail_notification( film_to_import )

