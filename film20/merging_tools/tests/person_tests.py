from django.test import TestCase
from django.contrib.auth.models import User

from film20.core.models import Person
from film20.merging_tools.forms import ReportPersonDuplicateForm

class DuplicatePersonsTestCase( TestCase ):
    
    def setUp( self ):
        self.u1 = User.objects.create_user( "user", "user@user.com", "user" )

        self.p1 = Person.objects.create( name='P1', surname='P1', type=Person.TYPE_PERSON )
        self.p2 = Person.objects.create( name='P2', surname='P2', type=Person.TYPE_PERSON )

    def tearDown( self ):
        User.objects.all().delete()
        Person.objects.all().delete()

    def testFormValidation( self ):
        form = ReportPersonDuplicateForm({ 'personA': self.p1.permalink, 'personB': self.p2.permalink })
        self.assertFalse( form.is_valid() )
