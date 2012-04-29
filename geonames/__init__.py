# -!- coding: utf-8 -!-
import re
from urllib2 import urlopen
from urllib import urlencode
import logging
from math import asin, sqrt, pow, sin, cos, pi
from django.conf import settings

try:
    from django.utils import simplejson as json
except ImportError:
    import json

def geo_distance(lat1, lng1, lat2, lng2):
    return 6371 * 2 * asin(sqrt(pow(sin((float(lat1) - abs(float(lat2))) * pi / 180 / 2), 2) + \
                      cos(float(lat1) * pi / 180 ) * cos(abs(float(lat2)) * pi/180) * pow(sin((float(lng1)-float(lng2)) * pi / 180 / 2), 2)))

def bounds(lat, lng, r):
    EARTH_R = 6367.449
    lat_delta = r / (pi / 180 * EARTH_R)
    lng_delta = r / (pi / 180 * cos(lat * pi/180) * EARTH_R)
    return lat + lat_delta, lat - lat_delta, lng + lng_delta, lng - lng_delta

def nearest_cities(lat, lng, r):
    b = bounds(float(lat), float(lng), float(r)) + (settings.GEONAMES_USERNAME, )
    data = urlopen('http://api.geonames.org/citiesJSON?north=%s&south=%s&east=%s&west=%s&lang=en&username=%s' % b).read()
    data = json.loads(data)
    return data['geonames']

def nearest_city(lat, lng, r):
    cities = nearest_cities(lat, lng, r)
    return cities and cities[0]
    
def timezone(lat, lng):
    data = urlopen('http://api.geonames.org/timezoneJSON?lat=%s&lng=%s&username=%s' % (lat, lng, settings.GEONAMES_USERNAME)).read()
    return json.loads(data)

if __name__ == "__main__":
    import sys
    lat, lng, r = map(float, (sys.argv[1:] + [15])[:3])
    print nearest_city(lat, lng, r)
