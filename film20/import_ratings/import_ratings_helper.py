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
from datetime import datetime
from BeautifulSoup import BeautifulSoup
import re, csv, cookielib
from urllib2 import urlopen as _urlopen, Request, URLError
from xml.dom import minidom
import time
from django.utils.translation import ugettext as _
from django.db.models import Q

from film20.core.search_helper import *
from film20.core.models import Object
from film20.core.models import Rating, ShortReview, Film, FilmLocalized
from film20.import_ratings.models import ImportRatings
from film20.import_ratings.models import ImportRatingsLog
from film20.import_films.models import ImportedFilm, FilmToImport

from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE
from film20.import_films import imdb_fetcher 

SCORE_TIER = 'tier'
SCORE_EXACT = 'score'
SCORE_AUTO = 'auto'
SCORE_DIV10 = 'score/10'
SCORE_CONVERTIONS = (
    (SCORE_AUTO, _('auto')),
    (SCORE_TIER, _('tier')),
    (SCORE_EXACT, _('exact')),
    (SCORE_DIV10, _('score/10')),
)

DEBUG = True

def escape_criticker_text(text):
    return text.replace('&amp;', '&')
    
def parse_criticker_votes(xml_file=None, xml_string = None, score_convertion=SCORE_AUTO, import_reviews=False):
    """
        Parses a file in Criticker XML format and returns a list of ratings
    """
    all_ratings = []
    if xml_file:
        DOMTree = minidom.parse(xml_file)
    elif xml_string:
        DOMTree = minidom.parseString(xml_string)
    else:
        print "Parsing criticker votes failed. Please provide either an xml_file or xml_string in parameters!"
        return None
        
    linkyear_pattern = re.compile('.*_(\d{4})/$')
    nodes = DOMTree.childNodes
    if score_convertion==SCORE_AUTO:
        min = max = None
        for i in nodes[0].getElementsByTagName('score'):
            score = int(i.childNodes[0].data)
            if not max or score>max: 
                max = score
            if not min or score<min:
                min = score
        span = max-min
        if span==0:
            span = 100
                
    for i in nodes[0].getElementsByTagName("film"):
        filmid = None
        filmwebid = None
        releaseyear = None
        if len(i.getElementsByTagName("filmid"))>0:
            filmid = i.getElementsByTagName("filmid")[0].childNodes[0].data

        # added for filmweb/imdb imports
        if len(i.getElementsByTagName("filmwebid"))>0:
            filmwebid = i.getElementsByTagName("filmwebid")[0].childNodes[0].data
        if len(i.getElementsByTagName("releaseyear"))>0:
            releaseyear = i.getElementsByTagName("releaseyear")[0].childNodes[0].data

        try:
            film_title = escape_criticker_text(i.getElementsByTagName("filmname")[0].childNodes[0].data)
        except Exception, e:
            # this happened in http://jira.filmaster.org/browse/FLM-304
            # TODO: investigate later why this fails for 1 row of test data in import_ratings/test/test_filmweb_rankings_anks.xml
            # TODO: XML docs here: http://docs.python.org/library/xml.dom.html
            print e
        review = None
        if import_reviews:
            try:
                review = escape_criticker_text(i.getElementsByTagName("quote")[0].childNodes[0].data)                        
            except:
                pass
        try:            
            if score_convertion==SCORE_TIER:
                score = int(i.getElementsByTagName("tier")[0].childNodes[0].data)
            elif score_convertion==SCORE_AUTO:
                score = int(i.getElementsByTagName("score")[0].childNodes[0].data)
                score = int(round(float(score-min)/(span) * 9 + 1))
            elif score_convertion==SCORE_DIV10:
                score = int(i.getElementsByTagName("score")[0].childNodes[0].data)
                score = int(round(float(score)/10))
            elif score_convertion==SCORE_EXACT:
                score = int(i.getElementsByTagName("score")[0].childNodes[0].data)
            if score<1:
                score = 1
            elif score>10:
                score = 10
        except:
            score = None
        movie = {'title':film_title, 'score':score, }

        if filmid:
            movie['criticker_id'] = filmid
        if filmwebid:
            movie['filmweb_id'] = filmwebid
        
        url = i.getElementsByTagName("filmlink")[0].childNodes[0].data
        
        yearmatch = linkyear_pattern.match(url)
        if releaseyear:
           movie['year'] = int(releaseyear)
        elif yearmatch and not film_title.endswith(yearmatch.group(1)):
            movie['year'] = int(yearmatch.group(1))
            
        if import_reviews and review:
            movie['review'] = review            
        all_ratings.append(movie)
    return all_ratings

def fetch_film_info_from_criticker(film_data):
    url = 'http://www.criticker.com/?f=' + film_data['criticker_id']
    title_page = None
    try:
        page = unicode(_urlopen(url, None, 5).read(), 'iso-8859-1')
        soup = BeautifulSoup(page)
        title_page = soup.find("div", attrs={"id":"fi_info_filmname"})
    except URLError, e:
        logger.error("URL Error: " + str(e.reason) + ": " + url)

    if title_page:
        full_title = title_page.contents[0]
        title = full_title.split("&nbsp;")
        title = title[0]

        akas_page = soup.findAll("div", attrs={"id": "fi_info_akas"})
        akas = []
        if akas_page:
            for aka in akas_page:
                alt_title = aka.contents[1].lstrip()
                akas.append(alt_title)
            akas.append(title)
        else:
            akas = None

        year_page = re.compile(".*\((\d{4})\)")
        fetch_year = re.match(year_page, full_title)
        year = int(fetch_year.groups(0)[0])

        film_data['imdb_id'] = ''
        
        imdb_page = soup.find("div", attrs={"id": "fi_info_imdb"})
        if imdb_page:
            imdb_url = soup.find("a", attrs={"target": "imdbwin"})
            imdb_regex = re.compile("\d{7}")
            imdb_id = re.findall(imdb_regex, str(imdb_url))[0]
            film_data['imdb_id'] = imdb_id

        film_data['year'] = year
        film_data['aka'] = akas
        film_data['title'] = title
        #print "fetched from %s for %s: year=%s, aka=%s" % (url, title, year, akas)
        if not year:
            try:
                print "WARN: Couldn't find year for %s (%s)" % (title.encode('utf-8'), str(url))
            except:
                print "WARN: Couldn't find year for a film. Exception when trying to print its title! Criticker ID: %s" % (str(film_data['criticker_id']))
    else:
        film_data['year'] = film_data['year'] if 'year' in film_data else None
        film_data['title'] = film_data['title'] if 'title' in film_data else None
        film_data['aka'] = None
        film_data['imdb_id'] = None
        logger.debug("Film %s doesn't exist on Criticker" % film_data['title'])

# Na bazie kodu Bola, dziekuje!
# Pobiera strone z ocenami z imdb.com
#
URLOPEN_DELAY=1
UA = "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)"

def urlopen(url, data=None, lang='en'):
    request = Request(url, data, {
        "Accept-Language": "%s,en-us;q=0.7,en;q=0.3"%lang.lower(),
        "User-Agent": UA,
    })
    logging.debug("urlopen: %s", url)
    time.sleep(URLOPEN_DELAY)
    return _urlopen(request)


def fetch_votes_from_imdb(imdbUrl):
    #cj = cookielib.CookieJar()
    #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    #imdbVoteHistory = opener.open(imdbUrl).read()
    imdbVoteHistory = urlopen(imdbUrl).read()
    return imdbVoteHistory
    
def escape_imdb_text(imdb_text):
    p = re.compile('&#(\d*);')
    p2 = re.compile('&#x([\da-fA-F]{2});')
    text = p.sub(lambda entity: unichr(int(entity.group(1))), imdb_text)             
    return p2.sub(lambda entity: unichr(int(entity.group(1), 16)), text)
    
def parse_imdb_votes(file):
    """
    Parse IMDB votes from CSV
    """
    all_ratings = []
    movie = None

    reader = csv.DictReader(file, delimiter=',', quotechar='"')
    for row in reader:
        id = row['const']
        id = id[2:]
        title = row['Title']
        year = row['Year']
        score = row['You rated']
        movie = {'imdb_id':id, 'title':title, 'year':int(year), 'score': int(score)}
        all_ratings.append(movie)
    return all_ratings

def search_film(film_title=None, year=None, imdb_id=None, criticker_id=None, filmweb_id=None):
    """
        Search for a film while importing ratings
    """
    from film20.utils.texts import normalized_text
    title_normalized = normalized_text(film_title)
    
    if imdb_id:
        try:
            film = Film.objects.get(imdb_code=imdb_id)
            if normalized_text(film.title)==title_normalized and (not year or year==film.release_year):
                return film
            else:
                logger.debug("WARN: not matching film! searching for: #%s %s (%s); found %s (%s)" %(imdb_id, film_title.encode('utf-8'), year, film.title.encode('utf-8'), film.release_year))
                # fix for http://jira.filmaster.org/browse/FLM-491
                # fetch movie by this imdb_code and check if year is same
                #   and title is in akas then return this film
                movie = imdb_fetcher.get_movie_by_id(  imdb_id, "http" )
                if movie:
                    if movie.get( 'year' ) == year:
                        akas = movie.get( 'akas' )
                        for aka in akas:
                            t, c = aka.split( '::' )
                            if t == film_title:
                                print " -- title is: %s" % c
                                return film
                    else:
                        logger.error("ERROR: this imdb_code is probably wrong ...")


        except Exception, e:
            logger.error("ERROR: %s" % e)
    if criticker_id:
        try:
            return Film.objects.get(criticker_id=str(criticker_id))
        except:
            pass
        
    # TODO enable when we have filmweb ids in database!
#    if filmweb_id:
#        try:
#            return Film.objects.filter(filmweb_id=str(filmweb_id))
#        except:
#            pass
            
    search_helper = Search_Helper()    
    search_results = search_helper.search_film(title=film_title)
    title_lower = film_title.lower()    
    best_results = list(search_results['best_results'])
    other_results = list(search_results['results'])
    if best_results==None:
        best_results = []
    if other_results==None:
        other_results = []
    all_results = best_results + other_results
    #print "all results for %s (%s): %s" % (film_title, year, ["%s (%s)" % (f.title, f.release_year) for f in all_results])
    if year:
        all_results = [f for f in all_results if f.release_year==year]
        #print "new all results for %s (%s): %s" % (film_title, year, ["%s (%s)" % (f.title, f.release_year) for f in all_results])
    exact, normalized, fuzzy = [], [], []
    def filter_films():
        for film in all_results:        
            e = n = f = False
            if film.title.lower()==title_lower:
                exact.append(film)
                e = True
            norm = normalized_text(film.title)
            if norm==title_normalized:
                normalized.append(film)
                n = True
            #if norm.startswith(title_normalized) or title_normalized.startswith(norm):
            if norm in title_normalized or title_normalized in norm:
                fuzzy.append(film)
                f = True
            if not e:
                for l in FilmLocalized.objects.filter(film=film.id):
                    if not e and l.title.lower()==title_lower:
                        exact.append(film)                        
                        e = True
                    norm = normalized_text(l.title)
                    if not n and norm==title_normalized:
                        normalized.append(film)                    
                        n = True
                    #if not f and (norm.startswith(title_normalized) or title_normalized.startswith(norm)):
                    if not f and (norm in title_normalized or title_normalized in norm):
                        fuzzy.append(film)
                        f = True
    filter_films()    

    if len(exact)==1:
        return exact[0]
    if len(normalized)==1:
        return normalized[0]
    #if year and len(fuzzy)==1:
    #    try:
    #        print "INFO: returning fuzzy match for %s (%s): %s (%s)" % (film_title, year, fuzzy[0].title, fuzzy[0].release_year)
    #    except UnicodeEncodeError:
    #        print "INFO: fuzzy match for %s(imdb) %s(criticker) (and unicode encode error problem!)" % (imdb_code, criticker_id)
    #    return fuzzy[0]
    #if not normalized and len(all_results)==1:
    #    return all_results[0]
    if year:
        all_results = best_results + other_results
        all_results = [f for f in all_results if abs(f.release_year-year)<=1]
        #exact = normalized = fuzzy = []        
        #if film_title=='I Am Guilty':
        #    print "before next filter: exact: %s; normalized: %s; fuzzy:%s" % (exact, normalized, fuzzy)        
        filter_films()
        #if film_title=='Battleship Potemkin':
        #    print "%s (%s) ~ exact: %s; normalized: %s; fuzzy:%s" % (film_title, year, exact, normalized, fuzzy)        
        if len(exact)==1:
            return exact[0]
        if len(normalized)==1:
            return normalized[0]
        #if len(fuzzy)==1:
        #    try:
        #        print "INFO: returning fuzzy match for %s (%s): %s (%s)" % (film_title, year, fuzzy[0].title, fuzzy[0].release_year)
        #    except UnicodeEncodeError:
        #        print "INFO: fuzzy match for %s(imdb) %s(criticker) (and unicode encode error problem!)" % (imdb_code, criticker_id)
        #    return fuzzy[0]
        #if len(all_results)==1:
        #    return all_results[0]                        
    #if year:
    #    print "%s (%s) ~ exact: %s; normalized: %s; fuzzy:%s" % (film_title, year, exact, normalized, fuzzy)        
    return None
        
from django.utils import simplejson as json    
def save_ratings_db(user, ratings, kind, overwrite=False):
    #films = u";;".join([ u"::".join([unicode(x) if x else "" for x in record]) for record in ratings])
    films = json.dumps(ratings)    

    print films
    ratings = ImportRatings(movies=films, user=user, overwrite=overwrite, kind=kind)
    ratings.save()
    
def save_rating(film, user, score=None, review=None, overwrite=False):
    """
        Saves a single rating to database
    """
    #f = lambda title, year: title if not year else title+" ("+str(year)+")"
    rated = False
    if score:
        score = int(float(score))
        link = film.parent.permalink
        try:
            rating = Rating.objects.get( parent = film,
                                               user = user, 
                                               type=Rating.TYPE_FILM)                
            if rating.rating:
                #movies_already_rated_list.append(film)
                #movies_already_rated = movies_already_rated + "; " + f(film.title, film.release_year)
                rated = True
            else:
                rating.first_rated = datetime.now()
        except Rating.DoesNotExist:
            rating = Rating.objects.create(user =user,
                        parent = film, 
                        film = film,
                        type = Rating.TYPE_FILM,
                        first_rated = datetime.now()
                    )
            
        if not rating.rating or overwrite:
            rating.rating = score
            rating.normalized = score
            rating.last_rated = datetime.now()
            rating.save()
            #movies_rated = movies_rated + "; " + f(film.title, film.release_year)
            #movies_rated_list.append(film)            
            
    if review and len(review)<ShortReview._meta.get_field('review_text').max_length:                
        # added hardcoding the short review language to EN
        try:
            sr = ShortReview.all_objects.get(
                kind = ShortReview.REVIEW,
                object=film, 
                user=user,
                LANG=settings.LANGUAGE_CODE)
            print "got review from db, updating for user_id=" + str(user.id) + ", object=" + str(film.id)
            # TODO: this delete is a hack for some stupid thing that makes it not work when simply updating 
            # (it tries to insert a new review in save() method)
            # CURRENTLY DISABLED (updates to short reviews won't be saved)
            # sr.delete()
            
        except ShortReview.DoesNotExist:            
            sr = ShortReview(                                 
                type = ShortReview.TYPE_SHORT_REVIEW,
                kind = ShortReview.REVIEW,
                permalink = 'FIXME',
                status = 1,
                version = 1, 
                object=film,
                user=user,
                LANG=settings.LANGUAGE_CODE,
            )
            print "review does not exist, creating with user_id=" + str(user.id) + ", object=" + str(film.id)

        if not sr.review_text or overwrite:
            sr.review_text = review
            try:
                sr.save()
                print "review saved"
            except Exception, e:
                print "review not saved, exception caught: " + str(e)
            
    return rated
    
    
def save_ratings(user, ratings, overwrite):
    """
        Saves a list of imported ratings for the selected user
    """
    movies_rated_list = []
    movies_already_rated_list = []
    titles_rated = []
    titles_already_rated = []
    titles_not_rated = []
    f = lambda title, year: title if not year else title+" ("+str(year)+")"
    f_imdb = lambda title, year, imdb_id: "#"+str(imdb_id)+":"+ (title if not year else title+" ("+str(year)+")")
    #import codecs
    #dest = codecs.open('c:/temp/import.html', 'w', 'utf-8')
    #dest.write('<html><body>')

    def rate_film(film, film_title, year, score, review, overwrite):
        was_rated = save_rating(film, user, score, review, overwrite)
        if was_rated:
            movies_already_rated_list.append(film)
            titles_already_rated.append(f(film_title, year))
        if overwrite or not was_rated:
            movies_rated_list.append(film)
            titles_rated.append(f(film_title, year))
    
    for record in ratings:
        film_title = record['title']
        year = record['year'] if 'year' in record else None
        score = record['score']        
        imdb_id = record['imdb_id'] if 'imdb_id' in record else None
        criticker_id = record['criticker_id'] if 'criticker_id' in record else None
        review = record['review'] if 'review' in record else None        
        aka = None

        if criticker_id is not None:
            fetch_film_info_from_criticker(record)
            imdb_id = record['imdb_id']
            year = record['year']
            film_title = record['title']
            aka = record['aka']

        film = None
        if aka is not None:
            for title in aka:
                logger.debug("try to search film %s by alternative title: %s (%s): %s" % (film_title, title, str(year), imdb_id))
                film = search_film(film_title=title, year=year, imdb_id=imdb_id)
                if film:
                    break
        else:
            logger.debug("try to search %s (%s): %s" % (film_title, str(year), imdb_id))
            film = search_film(film_title=film_title, year=year, imdb_id=imdb_id)

        if film:
            logger.info("found movie %s: rated at %s" % (film, score))
            rate_film(film, film_title, year, score, review, overwrite)
        else:
            logger.debug("film %s not found" % film_title)
            if imdb_id:
                logger.info("try to search by imdb_id: %s" % imdb_id)
                movie = imdb_fetcher.get_movie_by_id(imdb_id, "http")

                if movie:
                    film, status = imdb_fetcher.save_movie_to_db(movie)
                else:
                    logger.error("Probably given IMDB_ID: %s is not a movie" % imdb_id)
                
                if film:
                    if status == FilmToImport.ACCEPTED:
                        importedfilm = ImportedFilm(user=user, film=film)
                        importedfilm.save()
                        logger.info("imported movie %s" % film)
                    logger.info("found movie %s: rated at %s" % (film, score))
                    rate_film(film, film_title, year, score, review, overwrite)
                else:
                    logger.error("Failed to import movie!. Continuing import anyway...")

            if not film:
                logger.info("Film %s not rated" % film_title)
                titles_not_rated.append(f(film_title, year))
                #dest.write("<a href='http://filmaster.pl/dodaj-film/?%s'>%s</a><br/>\n" \
                #    % (urllib.urlencode({'title':f(film_title, year).encode('utf-8'), 'imdb_id':str(imdb_id) if imdb_id else ''}), f(film_title, year)))
                    
            
    movies_not_rated = "; ".join(titles_not_rated)
    rating_import_log = ImportRatingsLog(user=user, 
                                         movies_rated="; ".join(titles_rated),
                                         movies_already_rated = "; ".join(titles_already_rated),
                                         movies_not_rated= movies_not_rated)
    #dest.write('</body></html>')
    #dest.close()
    rating_import_log.save()
    return movies_rated_list, movies_already_rated_list, movies_not_rated

def fetch_votes_from_filmweb_simple(filmwebUrl):
    """
        Just fetch data from the given url address
    """
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.open(filmwebUrl)
    filmwebVH = opener.open(filmwebUrl).read()
    filmwebVH = filmwebVH.decode("utf-8")
    return filmwebVH

def fetch_votes_from_filmweb(filmweb_user):
    """
        Attempts to parse the Filmweb user page to fetch the file like
        http://www.filmweb.pl/splitString/user/21927/filmVotes
        being given an url like http://www.filmweb.pl/user/michuk
        by parsing that url, extracting the user ID, producing the destination url
        and fetching the file via http
        All explained here: http://jira.filmaster.org/browse/FLM-47
    """
    filmwebUrl = "http://www.filmweb.pl/user/" + str(filmweb_user)
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    filmweb_user_id = fetch_filmweb_user_id(opener, filmwebUrl)
    html = fetch_filmweb_votes(opener, filmweb_user_id)
    return html

def fetch_filmweb_user_id(opener, filmwebUrl):
    opener.open(filmwebUrl).read() # first one to omit the ads
    html = opener.open(filmwebUrl).read()

    for line in html.split('\n'):
        line = line.strip()
        firstLine = re.match('[^>]*/UserFavoritePersons\?id=(\d+)[^>]*', line)
        if firstLine <> None:
            filmweb_user_id = firstLine.group(1).strip()
            return filmweb_user_id
            
    return None

def fetch_filmweb_votes(opener, filmweb_user_id):    
    filmwebVotePage = 'http://www.filmweb.pl/splitString/user/'
    filmwebVotePage += filmweb_user_id + '/filmVotes'
    filmwebVH = opener.open(filmwebVotePage).read()
    return filmwebVH

def parse_filmweb_votes(filmwebVoteHistory):
    array = filmweb2array(filmwebVoteHistory)
    xml = filmweb2criticker(array)
    return xml

def filmweb2array(filmwebVoteHistory):
    """
        Extract an array of records with films and votes for further processing 
    """
    
    # prepare the string for import (remove UTF stuff, remove ampersands)
    filmwebVoteHistory = deogonkify(filmwebVoteHistory)
    filmwebVoteHistory = filmwebVoteHistory.replace("&", "&amp;") 
    
    films_array = filmwebVoteHistory.split('\\a')
    if not films_array:
        logger.error("Parsing error. Array with votes could not be constructed.")
        return []
    return films_array[7:len(films_array)]

def filmweb2criticker(films_array):
    """
        Parse the array with films and ratings to produce an XML file compatible with the
        XML produced by Criticker
    """

    cvh = '<recentrankings>\n'
    # sample value for "film" variable
    # \a[numer_filmu]\c[tytuł_oryginalny]\c[tytuł_polski (gdy nic -> tytuł polski jest taki sam jak oryginalny)]\c[rok]\c[ulubiony (0 - nie; 1 - tak)]\c[ocena]\c[adres_miniaturki_plakatu]\c[kod_kraju]\e[kod_następnego_kraju(opcjonalny, może być klka)\c[kod_gatunku]\e[kod_następnego_gatunku(opcjonalny, może być klka)\c[data_ocenienia: RRRRMMDD lub nic (brak oznacza, że film oceniono przed 20.10.2007)]
    for line in films_array:
        film_array = line.split('\\c')
        if film_array:
            filmweb_id = film_array[0]
            title = film_array[1]
            localized_title = film_array[2]
            release_year = film_array[3]
            favorite = film_array[4]
            rating = film_array[5]
            img = film_array[6]
            review_date = film_array[9]
#            print number + " | " + title + " | " + localized_title + " | " + release_year + " | " + favorite + " | " + rating

            cvh += '  <film>\n'
            cvh += '    <filmwebid>' + filmweb_id + '</filmwebid>\n'
            cvh += '    <filmname>' + title + '</filmname>\n'
            cvh += '    <releaseyear>' + release_year + '</releaseyear>\n'
            cvh += '    <filmlink>None</filmlink>\n' # TODO: fix the criticker parser so that it does not require this
            cvh += '    <img>http://gfx.filmweb.pl/po' + img + '</img>\n'
            cvh += '    <score>' + rating + '</score>\n'
            cvh += '    <quote/>\n'
            cvh += '    <reviewdate>' + review_date + '</reviewdate>\n'
            cvh += '    <tier>' + rating + '</tier>\n'
            cvh += '  </film>\n'
            continue
        else:
            logger.error("Could not parse a single line: " + line)

    cvh += '</recentrankings>\n'
    return cvh


def import_ratings():
    """
        Imports all ratings waiting to be imported in database
        Used in a cron job
    """
    ratings_to_import = ImportRatings.objects.filter(is_imported=False)
    for rating_to_import in ratings_to_import:
        movies_list = []
        if ';;' in rating_to_import.movies:
            movies = rating_to_import.movies.split(";;")
            for movie in movies:
                if movie != "":
                    rating_data = movie.split("::")
                    movies_list.append({'title':rating_data[0], 'score':rating_data[1]})
        else:
            movies_list = json.loads(rating_to_import.movies)
        overwrite = rating_to_import.overwrite;
        save_ratings(rating_to_import.user, movies_list, overwrite)
        rating_to_import.is_imported = True
        rating_to_import.imported_at = datetime.now()
        rating_to_import.save()
