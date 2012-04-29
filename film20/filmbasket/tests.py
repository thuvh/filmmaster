from datetime import datetime

from film20.utils.test import TestCase
from django.contrib.auth.models import User

from film20.core.models import Film, Rating
from film20.filmbasket.models import BasketItem

class FilmBasketTestCase( TestCase ):

    def setUp( self ):
        self.user = User.objects.create_user( "user", "user@user.com", "user" )

        self.film = Film( type=1, permalink='przypadek', imdb_code=111, status=1, version=1, \
                            release_year=1999, title='Przypadek' )
        self.film.save()



    def tearDown( self ):
        User.objects.all().delete()
        Film.objects.all().delete()
        Rating.objects.all().delete()
        BasketItem.objects.all().delete()

    def testRatingRemoveFromWishlist( self ):

        BasketItem.objects.create( film=self.film, wishlist=BasketItem.DYING_FOR, user=self.user )

        self.assertEqual( len( BasketItem.user_basket( self.user ) ), 1 )

        Rating.objects.create( type=Rating.TYPE_FILM, film=self.film, rating=5, 
                                parent=self.film, user=self.user)
    
        bi = BasketItem.objects.get( film=self.film, user=self.user )
        self.assertTrue( bi.wishlist is None )
