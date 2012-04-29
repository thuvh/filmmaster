# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ImportRatings'
        db.create_table('import_ratings_importratings', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('overwrite', self.gf('django.db.models.fields.BooleanField')(default=False, db_column='overwrite_rating')),
            ('kind', self.gf('django.db.models.fields.IntegerField')()),
            ('submited_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('imported_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('movies', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_imported', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('import_ratings', ['ImportRatings'])

        # Adding model 'ImportRatingsLog'
        db.create_table('import_ratings_importratingslog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('movies_rated', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('movies_already_rated', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('movies_not_rated', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('import_ratings', ['ImportRatingsLog'])


    def backwards(self, orm):
        
        # Deleting model 'ImportRatings'
        db.delete_table('import_ratings_importratings')

        # Deleting model 'ImportRatingsLog'
        db.delete_table('import_ratings_importratingslog')


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
        'followers.followers': {
            'Meta': {'ordering': "('-created_at',)", 'unique_together': "(('from_user', 'to_user', 'status'),)", 'object_name': 'Followers'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_users'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_users'", 'to': "orm['auth.User']"})
        },
        'import_ratings.importratings': {
            'Meta': {'object_name': 'ImportRatings'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'is_imported': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'kind': ('django.db.models.fields.IntegerField', [], {}),
            'movies': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'overwrite': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_column': "'overwrite_rating'"}),
            'submited_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'import_ratings.importratingslog': {
            'Meta': {'object_name': 'ImportRatingsLog'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'movies_already_rated': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'movies_not_rated': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'movies_rated': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['import_ratings']
