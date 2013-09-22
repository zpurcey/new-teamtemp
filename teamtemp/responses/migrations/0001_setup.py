# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'User'
        db.create_table(u'responses_user', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=8, primary_key=True)),
            ('session_token', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'responses', ['User'])

        # Adding model 'TeamTemperature'
        db.create_table(u'responses_teamtemperature', (
            ('id', self.gf('django.db.models.fields.CharField')(max_length=8, primary_key=True)),
            ('creation_date', self.gf('django.db.models.fields.DateField')()),
            ('duration', self.gf('django.db.models.fields.IntegerField')()),
            ('creator_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['responses.User'])),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal(u'responses', ['TeamTemperature'])

        # Adding model 'TemperatureResponse'
        db.create_table(u'responses_temperatureresponse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('request_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['responses.TeamTemperature'])),
            ('responder_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['responses.User'])),
            ('score', self.gf('django.db.models.fields.IntegerField')()),
            ('word', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'responses', ['TemperatureResponse'])


    def backwards(self, orm):
        # Deleting model 'User'
        db.delete_table(u'responses_user')

        # Deleting model 'TeamTemperature'
        db.delete_table(u'responses_teamtemperature')

        # Deleting model 'TemperatureResponse'
        db.delete_table(u'responses_temperatureresponse')


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
            'id': ('django.db.models.fields.CharField', [], {'max_length': '8', 'primary_key': 'True'}),
            'session_token': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['responses']