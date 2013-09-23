# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Rename field 'TeamTemperature.creator_id' to 'creator'
        db.rename_column(u'responses_teamtemperature', 'creator_id_id', 'creator_id')

        # Renaming field 'TemperatureResponse.responder_id' 'responder'
        db.rename_column(u'responses_temperatureresponse', 'responder_id_id', 
                'responder_id')

        # Renaming field 'TemperatureResponse.request_id' 'request'
        db.rename_column(u'responses_temperatureresponse', 'request_id_id', 'request_id')


    def backwards(self, orm):

        # Rename field 'TeamTemperature.creator' to 'creator_id'
        db.rename_column(u'responses_teamtemperature', 'creator_id', 'creator_id_id')

        # Renaming field 'TemperatureResponse.responder' 'responder_id'
        db.rename_column(u'responses_temperatureresponse', 'responder_id', 
                'responder_id_id')

        # Renaming field 'TemperatureResponse.request' 'request_id'
        db.rename_column(u'responses_temperatureresponse', 'request_id', 'request_id_id')


    models = {
        u'responses.teamtemperature': {
            'Meta': {'object_name': 'TeamTemperature'},
            'creation_date': ('django.db.models.fields.DateField', [], {}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['responses.User']"}),
            'duration': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '8', 'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'responses.temperatureresponse': {
            'Meta': {'object_name': 'TemperatureResponse'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['responses.TeamTemperature']"}),
            'responder': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['responses.User']"}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'word': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        u'responses.user': {
            'Meta': {'object_name': 'User'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '8', 'primary_key': 'True'})
        }
    }

    complete_apps = ['responses']
