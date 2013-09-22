from django import forms
import re

class CreateSurveyForm(forms.Form):
    duration = forms.IntegerField(required=False)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256)

class SurveyResponseForm(forms.Form):
    score = forms.IntegerField()
    word = forms.CharField(max_length=32)

    def clean_score(self):
        score = self.cleaned_data['score']
        if not re.match(r'[0-9]+'):
            raise forms.ValidationError('score should be a number')
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


