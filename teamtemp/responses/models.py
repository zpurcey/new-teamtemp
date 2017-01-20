import hashlib

import pytz
from datetime import timedelta
from django.db import models
from django.utils import timezone


class WordCloudImage(models.Model):
    id = models.AutoField(primary_key=True)
    word_hash = models.CharField(max_length=40, db_index=True)
    word_list = models.CharField(max_length=5000)
    image_url = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"{}: {} {} {} {}".format(self.id, self.creation_date, self.word_hash, self.word_list, self.image_url)

    def clean(self):
        self.word_list = self.word_list.lower().strip()
        self.word_hash = hashlib.sha1(self.word_list).hexdigest()


class User(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"{}: {}".format(self.id, self.creation_date)


def _stats_for(query_set):
    return {
               'count': query_set.count(),
               'average': query_set.aggregate(models.Avg('score')),
               'words': query_set.values('word').annotate(models.Count("id")).order_by()
           }, query_set


class TeamTemperature(models.Model):
    TEAM_TEMP = 'TEAMTEMP'
    DEPT_REGION_SITE = 'DEPT-REGION-SITE'
    CUSTOMER_FEEDBACK = 'CUSTOMERFEEDBACK'

    SURVEY_TYPE_CHOICES = (
        (TEAM_TEMP, 'Team Temperature'),
        (DEPT_REGION_SITE, 'Department-Region-Site Temperature'),
        (CUSTOMER_FEEDBACK, 'Customer Feedback'),
    )

    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]

    id = models.CharField(max_length=8, primary_key=True)
    creator = models.ForeignKey(User, related_name="team_temperatures")
    password = models.CharField(max_length=256)
    archive_schedule = models.PositiveSmallIntegerField(default=0)
    archive_date = models.DateTimeField(blank=True, null=True)
    next_archive_date = models.DateField(blank=True, null=True)
    survey_type = models.CharField(default=TEAM_TEMP, choices=SURVEY_TYPE_CHOICES, max_length=20, db_index=True)
    dept_names = models.CharField(blank=True, null=True, max_length=64)
    region_names = models.CharField(blank=True, null=True, max_length=64)
    site_names = models.CharField(blank=True, null=True, max_length=64)
    default_tz = models.CharField(default='Australia/Queensland', choices=TIMEZONE_CHOICES, max_length=64)
    max_word_count = models.PositiveSmallIntegerField(default=1)
    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def stats(self):
        return _stats_for(self.temperature_responses.filter(archived=False))

    def team_stats(self, team_name_list):
        return _stats_for(self.temperature_responses.filter(team_name__in=team_name_list, archived=False))

    def archive_stats(self, archive_date):
        return _stats_for(self.temperature_responses.filter(archived=True, archive_date=archive_date))

    def archive_team_stats(self, team_name_list, archive_date):
        return _stats_for(
            self.temperature_responses.filter(team_name__in=team_name_list, archive_date=archive_date, archived=True))

    def accumulated_stats(self, start_date, end_date):
        return _stats_for(self.temperature_responses.filter(response_date__gte=end_date, response_date__lte=start_date))

    def accumulated_team_stats(self, team_name_list, start_date, end_date):
        return _stats_for(self.temperature_responses.filter(team_name__in=team_name_list, response_date__gte=end_date,
                                                            response_date__lte=start_date))

    def fill_next_archive_date(self, overwrite=False):
        if self.archive_schedule > 0:
            if self.next_archive_date is None or overwrite:
                if self.archive_date is not None:
                    self.next_archive_date = (self.archive_date + timedelta(days=self.archive_schedule)).date()
                else:
                    self.next_archive_date = timezone.now().date()
        elif overwrite:
            self.next_archive_date = None

        return self.next_archive_date

    def advance_next_archive_date(self):
        if self.archive_schedule > 0:
            if self.next_archive_date is None:
                self.fill_next_archive_date()

            now = timezone.now().date()
            while self.next_archive_date < now:
                self.next_archive_date = self.next_archive_date + timedelta(days=self.archive_schedule)

        return self.next_archive_date

    def __unicode__(self):
        return u"{}: {} {} {} {} {} {} {} {} {}".format(self.id, self.creator.id,
                                                        self.creation_date, self.archive_schedule, self.archive_date,
                                                        self.survey_type, self.region_names, self.region_names,
                                                        self.site_names, self.default_tz)


class TemperatureResponse(models.Model):
    # class Meta:
    #     unique_together = ("request", "responder", "team_name", "archive_date")

    id = models.AutoField(primary_key=True)
    request = models.ForeignKey(TeamTemperature, related_name="temperature_responses")
    responder = models.ForeignKey(User, related_name="temperature_responses")
    score = models.PositiveSmallIntegerField()
    word = models.CharField(max_length=32)
    team_name = models.CharField(max_length=64, db_index=True)
    archived = models.BooleanField(default=False, db_index=True)
    response_date = models.DateTimeField(db_index=True)
    archive_date = models.DateTimeField(blank=True, null=True, db_index=True)

    def __unicode__(self):
        return u"{}: {} {} {} {} {} {} {} {}".format(self.id, self.request.id,
                                                     self.responder.id,
                                                     self.score, self.word, self.team_name,
                                                     self.archived, self.response_date,
                                                     self.archive_date)

    def clean(self):
        self.word = self.word.lower().strip()


class TeamResponseHistory(models.Model):
    class Meta:
        verbose_name_plural = "Team response histories"

    id = models.AutoField(primary_key=True)
    request = models.ForeignKey(TeamTemperature, related_name="team_response_histories")
    average_score = models.DecimalField(decimal_places=5, max_digits=10)
    word_list = models.CharField(max_length=5000)
    responder_count = models.PositiveSmallIntegerField()
    team_name = models.CharField(max_length=64, null=True, db_index=True)
    archive_date = models.DateTimeField(db_index=True)

    def __unicode__(self):
        return u"{}: {} {} {} {} {} {}".format(self.id, self.request.id,
                                               self.average_score,
                                               self.word_list, self.responder_count,
                                               self.team_name, self.archive_date)

    def clean(self):
        self.word_list = self.word_list.lower().strip()


class Teams(models.Model):
    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        unique_together = ("request", "team_name")

    id = models.AutoField(primary_key=True)
    request = models.ForeignKey(TeamTemperature, related_name="teams")
    team_name = models.CharField(max_length=64, db_index=True)
    dept_name = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    site_name = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    region_name = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def pretty_team_name(self):
        return self.team_name.replace('_', ' ')

    def __unicode__(self):
        return u"{}: {} {} {} {} {}".format(self.id, self.request.id,
                                            self.team_name, self.dept_name, self.site_name, self.region_name)
