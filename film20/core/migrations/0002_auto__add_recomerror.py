# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'RecomError'
        db.create_table('core_recomerror', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('sum', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=16, decimal_places=8)),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('core', ['RecomError'])


    def backwards(self, orm):
        
        # Deleting model 'RecomError'
        db.delete_table('core_recomerror')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'followers': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_to'", 'symmetrical': 'False', 'through': "orm['followers.Followers']", 'to': "orm['auth.User']"}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.character': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'Character'},
            'character': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description_full': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'description_lead': ('django.db.models.fields.CharField', [], {'max_length': '350', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_thumb_lost': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'importance': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Person']"})
        },
        'core.country': {
            'Meta': {'object_name': 'Country'},
            'country': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'core.deferredtask': {
            'Meta': {'object_name': 'DeferredTask'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.TextField', [], {}),
            'eta': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_tries': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'queue_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'try_cnt': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'core.film': {
            'Meta': {'object_name': 'Film'},
            'actors': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'films_played'", 'to': "orm['core.Person']", 'through': "orm['core.Character']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'criticker_id': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'directors': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'films_directed'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['core.Person']"}),
            'hires_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'imdb_code': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'is_enh9': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Object']", 'unique': 'True', 'primary_key': 'True'}),
            'popularity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'production_country': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'produced_in'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['core.Country']"}),
            'production_country_list': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'release_year': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'title_normalized': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'tmdb_import_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'verified_imdb_code': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'writers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'screenplays_written'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['core.Person']"})
        },
        'core.filmcomparator': {
            'Meta': {'object_name': 'FilmComparator'},
            'compared_film': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'compared_films'", 'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_film': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'main_films'", 'to': "orm['core.Film']"}),
            'score': ('django.db.models.fields.DecimalField', [], {'default': "'0.000'", 'max_digits': '5', 'decimal_places': '3'})
        },
        'core.filmlocalized': {
            'Meta': {'object_name': 'FilmLocalized', '_ormbases': ['core.ObjectLocalized']},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '15000', 'null': 'True', 'blank': 'True'}),
            'fetched_description': ('django.db.models.fields.CharField', [], {'max_length': '15000', 'null': 'True', 'blank': 'True'}),
            'fetched_description_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fetched_description_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'fetched_description_url_text': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'object_localized': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.ObjectLocalized']", 'unique': 'True', 'primary_key': 'True'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'release_year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'title_normalized': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'core.filmlog': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'FilmLog'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '40000', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'localized_title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'release_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'release_year': ('django.db.models.fields.IntegerField', [], {}),
            'saved_by': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'version_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'core.filmranking': {
            'Meta': {'object_name': 'FilmRanking'},
            'average_score': ('django.db.models.fields.DecimalField', [], {'max_digits': '4', 'decimal_places': '2'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_votes': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {})
        },
        'core.localizedprofile': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'unique_together': "(('user', 'LANG'),)", 'object_name': 'LocalizedProfile'},
            'blog_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.moderatedfilmlocalized': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'ModeratedFilmLocalized'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '15000', 'null': 'True', 'blank': 'True'}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Film']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderation_status': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'moderation_status_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'moderation_status_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'moderatedfilmlocalized_moderated_objects'", 'null': 'True', 'to': "orm['auth.User']"}),
            'rejection_reason': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.object': {
            'Meta': {'object_name': 'Object'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_comments': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permalink': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        },
        'core.objectlocalized': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'ObjectLocalized'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Object']"}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'core.person': {
            'Meta': {'ordering': "['surname']", 'object_name': 'Person'},
            'actor_popularity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'actor_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'day_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'director_popularity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'director_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'hires_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'imdb_code': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'is_actor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_writer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'month_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Object']", 'unique': 'True', 'primary_key': 'True'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'tmdb_import_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'verified_imdb_code': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'writer_popularity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'writer_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'year_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'core.personlocalized': {
            'Meta': {'object_name': 'PersonLocalized', '_ormbases': ['core.ObjectLocalized']},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'object_localized': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.ObjectLocalized']", 'unique': 'True', 'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Person']"}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'core.personlog': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'PersonLog'},
            'actor_popularity': ('django.db.models.fields.IntegerField', [], {}),
            'actor_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '40000', 'null': 'True', 'blank': 'True'}),
            'day_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'director_popularity': ('django.db.models.fields.IntegerField', [], {}),
            'director_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_actor': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_director': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_writer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'month_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Person']"}),
            'saved_by': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'surname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'tag_list': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'version_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'writer_popularity': ('django.db.models.fields.IntegerField', [], {}),
            'writer_popularity_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'year_of_birth': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'core.profile': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'Profile'},
            'aol': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'country': ('film20.userprofile.countries.CountryField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'criticker_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'facebook_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'foursquare_access_token': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'foursquare_user_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'gg': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'icq': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imdb_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'iphone_token': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'jabber_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'metacritic_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'mobile_first_login_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mobile_last_login_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'mobile_login_cnt': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'mobile_platform': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'msn': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'myspace_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'recommendations_notice_sent': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'recommendations_status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'registration_source': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timezone_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'twitter_access_token': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'twitter_user_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'core.rating': {
            'Meta': {'object_name': 'Rating'},
            'actor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rated_as_actor'", 'null': 'True', 'to': "orm['core.Person']"}),
            'director': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'rated_as_director'", 'null': 'True', 'to': "orm['core.Person']"}),
            'film': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'film_ratings'", 'null': 'True', 'to': "orm['core.Film']"}),
            'first_rated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'guess_rating_alg1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'guess_rating_alg2': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_displayed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'last_rated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'normalized': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'number_of_comments': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'number_of_ratings': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Object']"}),
            'rating': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.ratingcomparator': {
            'Meta': {'object_name': 'RatingComparator'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'common_films': ('django.db.models.fields.IntegerField', [], {}),
            'compared_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'compared_users'", 'to': "orm['auth.User']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'main_users'", 'to': "orm['auth.User']"}),
            'previous_save_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'score': ('django.db.models.fields.DecimalField', [], {'max_digits': '4', 'decimal_places': '2'}),
            'score2': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '4', 'decimal_places': '2'}),
            'sum_difference': ('django.db.models.fields.IntegerField', [], {}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'core.recomerror': {
            'Meta': {'object_name': 'RecomError'},
            'count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sum': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '16', 'decimal_places': '8'})
        },
        'core.recommendation': {
            'Meta': {'object_name': 'Recommendation'},
            'film': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'film_recommendation'", 'null': 'True', 'to': "orm['core.Film']"}),
            'guess_rating_alg1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'guess_rating_alg2': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '4', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.searchkey': {
            'Meta': {'object_name': 'SearchKey'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_letters': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'key_normalized': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'key_root': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Object']"}),
            'object_localized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ObjectLocalized']", 'null': 'True', 'blank': 'True'}),
            'text_length': ('django.db.models.fields.IntegerField', [], {})
        },
        'core.shortreview': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'ShortReview', '_ormbases': ['core.Object']},
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            'kind': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'object': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'short_reviews'", 'null': 'True', 'to': "orm['core.Object']"}),
            'parent': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.Object']", 'unique': 'True', 'primary_key': 'True'}),
            'rating': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'short_reviews'", 'null': 'True', 'to': "orm['core.Rating']"}),
            'review_text': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'core.shortreviewold': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'ShortReviewOld'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rating': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'short_reviewsold'", 'to': "orm['core.Rating']"}),
            'review_text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'core.userratingtimerange': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'object_name': 'UserRatingTimeRange'},
            'first_rated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_rated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'followers.followers': {
            'Meta': {'ordering': "('-created_at',)", 'unique_together': "(('from_user', 'to_user', 'status'),)", 'object_name': 'Followers'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': "orm['auth.User']"})
        },
        'tagging.tag': {
            'LANG': ('django.db.models.fields.CharField', [], {'default': "'pl'", 'max_length': '2'}),
            'Meta': {'ordering': "('name',)", 'object_name': 'Tag'},
            'category': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'tagging.taggeditem': {
            'Meta': {'unique_together': "(('tag', 'content_type', 'object_id'),)", 'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['tagging.Tag']"})
        }
    }

    complete_apps = ['core']
