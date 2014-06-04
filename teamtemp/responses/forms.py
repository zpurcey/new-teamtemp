from django import forms
from django.forms.util import ErrorList
from teamtemp.responses.models import TemperatureResponse
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re

class ErrorBox(ErrorList):
    def __unicode__(self):
        return mark_safe(self.as_box())

    def as_box(self):
        if not self: return u''
        return u'<div class="error box">%s</div>' % self.as_lines()

    def as_lines(self):
        return "<br/>".join(e for e in self)

class CreateSurveyForm(forms.Form):
    error_css_class='error box'
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256)
    team_name = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64)
    
    def clean_team_name(self):
        team_name = self.cleaned_data['team_name']
        matches = re.findall(r'[^A-Za-z0-9 \'-]', team_name)
        if matches:
            error = '"{team_name}" contains invalid characters '\
                    '{matches}'.format(team_name=escape(team_name), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return team_name

class AddTeamForm(forms.Form):
    error_css_class='error box'
    team_name = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64)
    
    def clean_team_name(self):
        team_name = self.cleaned_data['team_name']
        matches = re.findall(r'[^A-Za-z0-9 \'-]', team_name)
        if matches:
            error = '"{team_name}" contains invalid characters '\
                    '{matches}'.format(team_name=escape(team_name), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return team_name


class SurveyResponseForm(forms.ModelForm):
    class Meta:
        model = TemperatureResponse
        fields = ['score', 'word']

    def clean_score(self):
        score = self.cleaned_data['score']
        if int(score) < 1:
            raise forms.ValidationError('temperature %d is too low' % score)
        if int(score) > 10:
            raise forms.ValidationError('temperature %d is too high' % score)
        return score

    def clean_word(self):
        word = self.cleaned_data['word']
        matches = re.findall(r'[^A-Za-z0-9\'-]', word)
        if matches:
            error = '"{word}" contains invalid characters '\
                    '{matches}'.format(word=escape(word), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return word

class ResultsPasswordForm(forms.Form):
    error_css_class='error box'
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256)
