# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'User.session_token'
        db.delete_column(u'responses_user', 'session_token')


    def backwards(self, orm):
        # Adding field 'User.session_token'
        db.add_column(u'responses_user', 'session_token',
                      self.gf('django.db.models.fields.CharField')(default='bobbins', max_length=32),
                      keep_default=False)


    models = {
        u'responses.teamtemperature': {
            'Meta': {'object_name': 'TeamTemperature'},
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'creator_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['responses.User']"}),
            'duration': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '8', 'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'responses.temperatureresponse': {
            'Meta': {'object_name': 'TemperatureResponse'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['responses.TeamTemperature']"}),
            'responder_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['responses.User']"}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'word': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'responses.user': {
            'Meta': {'object_name': 'User'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '8', 'primary_key': 'True'})
        }
    }

    complete_apps = ['responses']