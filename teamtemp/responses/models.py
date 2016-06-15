from django.db import models

class WordCloudImage(models.Model):
    creation_date = models.DateField()
    word_list = models.CharField(max_length=5000)
    image_url = models.CharField(max_length=255)

    def __unicode__(self):
        return u"{} {} {}".format(self.creation_date, self.word_list, image_url)


class User(models.Model):
    id = models.CharField(max_length=8, primary_key=True)

    def __unicode__(self):
        return u"{}".format(self.id)


class TeamTemperature(models.Model):
    id = models.CharField(max_length=8, primary_key=True)
    creation_date = models.DateField()
    creator = models.ForeignKey(User)
    password = models.CharField(max_length=256)
    archive_schedule = models.IntegerField(default=0)
    archive_date = models.DateTimeField(null=True)
    survey_type = models.CharField(default='TEAMTEMP',max_length=20)
    dept_names = models.CharField(default='DEPT,DEPT2',max_length=64)
    region_names = models.CharField(default='REGION,REGION2',max_length=64)
    site_names = models.CharField(default='SITE,SITE2',max_length=64)
    default_tz = models.CharField(default='Australia/Queensland',max_length=64)
    max_word_count = models.IntegerField(default=1)
    
    def _stats_for(self, query_set):
        result = dict()
        result['count'] = query_set.count()
        result['average'] = query_set.aggregate(models.Avg('score'))
        result['words'] = query_set.values('word').annotate(models.Count("id")).order_by()
        return result 

    def stats(self):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(archived = False)
        return self._stats_for(allresponses) 

    def team_stats(self, team_name):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(team_name__in = team_name, archived = False)
        return self._stats_for(allresponses) 

    def archive_stats(self, archive_date):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(archived = True,archive_date = archive_date)
        return self._stats_for(allresponses) 

    def archive_team_stats(self, team_name, archive_date):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(team_name__in = team_name, archive_date = archive_date, archived = True)
        return self._stats_for(allresponses)  

    def accumulated_stats(self, start_date, end_date):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(response_date__gte=end_date, response_date__lte=start_date)
        return self._stats_for(allresponses) 

    def accumulated_team_stats(self, team_name, start_date, end_date):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(team_name__in = team_name, response_date__gte=end_date, response_date__lte=start_date)
        return self._stats_for(allresponses) 

    def __unicode__(self):
        return u"{}: {} {} {} {} {} {} {} {} {}".format(self.id, self.creator.id,
                                   self.creation_date, self.archive_schedule, self.archive_date,
                                   self.survey_type, self.region_names, self.region_names,
                                   self.site_names, self.default_tz)


class TemperatureResponse(models.Model):
    request = models.ForeignKey(TeamTemperature)
    responder = models.ForeignKey(User)
    score = models.IntegerField()
    word = models.CharField(max_length=32)
    team_name = models.CharField(max_length=64, null=True)
    archived = models.BooleanField(default=False)
    response_date = models.DateTimeField(null=True)
    archive_date = models.DateTimeField(null=True)

    def __unicode__(self):
        return u"{}: {} {} {} {} {} {} {} {}".format(self.id, self.request.id, 
                                         self.responder.id,
                                         self.score, self.word, self.team_name,
                                         self.archived, self.response_date,
                                         self.archive_date)

class TeamResponseHistory(models.Model):
    request = models.ForeignKey(TeamTemperature)
    average_score = models.DecimalField(decimal_places=5, max_digits=10)
    word_list = models.CharField(max_length=5000)
    responder_count = models.IntegerField()
    team_name = models.CharField(max_length=64, null=True)
    archive_date = models.DateTimeField()

    def __unicode__(self):
        return u"{}: {} {} {} {} {} {}".format(self.id, self.request.id, 
                                         self.average_score,
                                         self.word_list, self.responder_count,
                                         self.team_name, self.archive_date)

class Teams(models.Model):
    request = models.ForeignKey(TeamTemperature)
    team_name = models.CharField(max_length=64, null=True)
    dept_name = models.CharField(max_length=64, null=True)
    site_name = models.CharField(max_length=64, null=True)
    region_name = models.CharField(max_length=64, null=True)

    def pretty_team_name(self):
        return self.team_name.replace('_', ' ')

    def __unicode__(self):
        return u"{}: {} {} {} {} {}".format(self.id, self.request.id,
                                         self.team_name, self.dept_name, self.site_name, self.region_name)
