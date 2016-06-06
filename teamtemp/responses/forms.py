from django import forms
from django.forms.utils import ErrorList
from teamtemp.responses.models import TemperatureResponse, TeamTemperature, Teams
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re
import pytz

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
    dept_names = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False, label='DEPT1,DEPT2..', help_text='DEPT1,DEPT2..')
    region_names = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False, label='REGION1,REGION2..',help_text='REGION1,REGION2..')
    site_names = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False, label='SITE1,SITE2..',help_text='SITE1,SITE2..')

    def clean_dept_names(self):
        dept_names = self.cleaned_data['dept_names']
        matches = re.findall(r'[^A-Za-z0-9\'-,]', dept_names)
        if matches:
            error = '"{dept_names}" contains invalid characters '\
                    '{matches}'.format(dept_names=escape(dept_names), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return dept_names

    def clean_region_names(self):
        region_names = self.cleaned_data['region_names']
        matches = re.findall(r'[^A-Za-z0-9\'-,]', region_names)
        if matches:
            error = '"{region_names}" contains invalid characters '\
                    '{matches}'.format(regions_names=escape(region_names), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return region_names

    def clean_site_names(self):
        site_names = self.cleaned_data['site_names']
        matches = re.findall(r'[^A-Za-z0-9\'-,]', site_names)
        if matches:
            error = '"{site_names}" contains invalid characters '\
                    '{matches}'.format(site_names=escape(site_names), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return site_names

class FilteredBvcForm(forms.Form):
    error_css_class='error box'
    
    def __init__(self, *args, **kwargs):
        dept_names_list = kwargs.pop('dept_names_list')
        region_names_list = kwargs.pop('region_names_list')
        site_names_list = kwargs.pop('site_names_list')
        dept_names_list_on = kwargs.pop('dept_names_list_on')
        region_names_list_on = kwargs.pop('region_names_list_on')
        site_names_list_on = kwargs.pop('site_names_list_on')
        super(FilteredBvcForm, self).__init__(*args, **kwargs)
        self.fields['filter_dept_names'] = forms.MultipleChoiceField(choices=[(x,x)for x in dept_names_list],widget=forms.CheckboxSelectMultiple,required=False,initial=dept_names_list_on)
        self.fields['filter_region_names'] = forms.MultipleChoiceField(choices=[(x,x)for x in region_names_list],widget=forms.CheckboxSelectMultiple,required=False,initial=region_names_list_on)
        self.fields['filter_site_names'] = forms.MultipleChoiceField(choices=[(x,x)for x in site_names_list],widget=forms.CheckboxSelectMultiple,required=False,initial=site_names_list_on)

    def clean_filter_dept_names(self):
        filter_dept_names = self.cleaned_data['filter_dept_names']
        for dept_name in filter_dept_names:
            matches = re.findall(r'[^A-Za-z0-9 \'-]', dept_name)
            if matches:
                error = '"{dept_name}" contains invalid characters '\
                        '{matches}'.format(dept_name=escape(dept_name), matches=list({str(x) for x in matches}))
                raise forms.ValidationError(error)
        return filter_dept_names

    def clean_filter_site_names(self):
        filter_site_names = self.cleaned_data['filter_site_names']
        for site_name in filter_site_names:
            matches = re.findall(r'[^A-Za-z0-9 \'-]', site_name)
            if matches:
                error = '"{site_name}" contains invalid characters '\
                        '{matches}'.format(site_name=escape(site_name), matches=list({str(x) for x in matches}))
                raise forms.ValidationError(error)
        return filter_site_names

    def clean_filter_region_names(self):
        filter_region_names = self.cleaned_data['filter_region_names']
        for region_name in filter_region_names:
            matches = re.findall(r'[^A-Za-z0-9 \'-]', region_name)
            if matches:
                error = '"{region_name}" contains invalid characters '\
                    '{matches}'.format(region_name=escape(region_name), matches=list({str(x) for x in matches}))
                raise forms.ValidationError(error)
        return filter_region_names

class AddTeamForm(forms.ModelForm):
    class Meta:
        model = Teams
        fields = ['team_name','dept_name','region_name','site_name']

    error_css_class='error box'
    team_name = forms.CharField(max_length=64)
    dept_name = forms.CharField(max_length=64)
    site_name = forms.CharField(max_length=64)
    region_name = forms.CharField(max_length=64)
    
    def __init__(self, *args, **kwargs):
        dept_names_list = kwargs.pop('dept_names_list')
        region_names_list = kwargs.pop('region_names_list')
        site_names_list = kwargs.pop('site_names_list')
        super(AddTeamForm, self).__init__(*args, **kwargs)
        self.fields['dept_name'] = forms.ChoiceField(choices=[(x,x)for x in dept_names_list],required=False)
        self.fields['region_name'] = forms.ChoiceField(choices=[(x,x)for x in region_names_list],required=False)
        self.fields['site_name'] = forms.ChoiceField(choices=[(x,x)for x in site_names_list],required=False)

    def clean_team_name(self):
        team_name = self.cleaned_data['team_name']
        matches = re.findall(r'[^A-Za-z0-9 \'-]', team_name)
        if matches:
            error = '"{team_name}" contains invalid characters '\
                    '{matches}'.format(team_name=escape(team_name), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return team_name

    def clean_dept_name(self):
        dept_name = self.cleaned_data['dept_name']
        matches = re.findall(r'[^A-Za-z0-9 \'-]', dept_name)
        if matches:
            error = '"{dept_name}" contains invalid characters '\
                    '{matches}'.format(dept_name=escape(dept_name), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return dept_name

    def clean_site_name(self):
        site_name = self.cleaned_data['site_name']
        matches = re.findall(r'[^A-Za-z0-9 \'-]', site_name)
        if matches:
            error = '"{site_name}" contains invalid characters '\
                    '{matches}'.format(site_name=escape(site_name), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return site_name

    def clean_region_name(self):
        region_name = self.cleaned_data['region_name']
        matches = re.findall(r'[^A-Za-z0-9 \'-]', region_name)
        if matches:
            error = '"{region_name}" contains invalid characters '\
                    '{matches}'.format(region_name=escape(region_name), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return region_name

class SurveyResponseForm(forms.ModelForm):
    class Meta:
        model = TemperatureResponse
        fields = ['score', 'word']

    score = forms.CharField(label='')
    word = forms.CharField(label='')
    
    def __init__(self, *args, **kwargs):
        self.max_word_count = kwargs.pop('max_word_count')
        super(SurveyResponseForm, self).__init__(*args, **kwargs)


    def clean_score(self):
        score = self.cleaned_data['score']
        if not score.isdigit():
            raise forms.ValidationError('Temperature %s may contain numbers only' % score)
        if int(score) < 1:
            raise forms.ValidationError('Temperature %s is too low' % score)
        if int(score) > 10:
            raise forms.ValidationError('Temperature %s is too high' % score)
        return score

    def clean_word(self):
        word = self.cleaned_data['word']
        matches = re.findall(r'[^A-Za-z0-9 \'-]', word)
        if matches:
            error = '"{word}" contains invalid characters '\
                    '{matches}'.format(word=escape(word), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        
        word_count = len(word.split())
        if word_count > self.max_word_count:
            error = 'Max {max_word_count} Words'.format(max_word_count=escape(self.max_word_count))
            raise forms.ValidationError(error)

        return word

class ResultsPasswordForm(forms.Form):
    error_css_class='error box'
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256)

class SurveySettingsForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256, required=False)
    new_team_name = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False)
    current_team_name = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False)
    censored_word = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False)
    dept_names = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False)
    region_names = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False)
    site_names = forms.CharField(widget=forms.TextInput(attrs={'size': '64'}), max_length=64, required=False)
    default_tz = forms.ChoiceField(choices=[(x,x)for x in pytz.all_timezones],required=False)
    
    
    class Meta:
        model = TeamTemperature
        fields = ['archive_schedule', 'survey_type','dept_names','region_names','site_names','default_tz','max_word_count']
    
    def clean_archive_schedule(self):
        archive_schedule = self.cleaned_data['archive_schedule']
        if int(archive_schedule) > 28:
            raise forms.ValidationError('Archive Schedule Max 28 Days')
        return archive_schedule
    
    def clean_survey_type(self):
        survey_type = self.cleaned_data['survey_type']
        if survey_type not in ['TEAMTEMP', 'CUSTOMERFEEDBACK', 'DEPT-REGION-SITE']:
            raise forms.ValidationError('Supported Survey Types: TEAMTEMP and CUSTOMERFEEDBACK only')
        return survey_type

    def clean_dept_names(self):
        dept_names = self.cleaned_data['dept_names']
        matches = re.findall(r'[^A-Za-z0-9\'-,]', dept_names)
        if matches:
            error = '"{dept_names}" contains invalid characters '\
                '{matches}'.format(dept_names=escape(dept_names), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return dept_names

    def clean_region_names(self):
        region_names = self.cleaned_data['region_names']
        matches = re.findall(r'[^A-Za-z0-9\'-,]', region_names)
        if matches:
            error = '"{region_names}" contains invalid characters '\
                '{matches}'.format(regions_names=escape(region_names), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return region_names

    def clean_site_names(self):
        site_names = self.cleaned_data['site_names']
        matches = re.findall(r'[^A-Za-z0-9\'-,]', site_names)
        if matches:
            error = '"{site_names}" contains invalid characters '\
                '{matches}'.format(site_names=escape(site_names), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return site_names

    def clean_default_tz(self):
        default_tz = self.cleaned_data['default_tz']
        matches = re.findall(r'[^A-Za-z0-9\'-/,]', default_tz)
        if matches:
            error = '"{default_tz}" contains invalid characters '\
                '{matches}'.format(default_tz=escape(default_tz), matches=list({str(x) for x in matches}))
            raise forms.ValidationError(error)
        return default_tz

    def clean_max_word_count(self):
        max_word_count = self.cleaned_data['max_word_count']
        if int(max_word_count) > 5:
            raise forms.ValidationError('Max Word Count Max Value = 5')
        return max_word_count

