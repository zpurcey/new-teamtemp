from django import forms
from responses.models import TemperatureResponse
import re

class CreateSurveyForm(forms.Form):
    duration = forms.IntegerField(required=False)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256)

class SurveyResponseForm(forms.ModelForm):
    class Meta:
        model = TemperatureResponse
        fields = ['score', 'word']

    def clean_score(self):
        score = self.cleaned_data['score']
        if int(score) < 1:
            raise forms.ValidationError('score is too low')
        if int(score) > 10:
            raise forms.ValidationError('score is too high')
        return score

    def clean_word(self):
        word = self.cleaned_data['word']
        if re.match(r'[^A-Za-z0-9\'-]', word):
            raise forms.ValidationError('word contains invalid characters')
        return word

class ResultsPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256)
