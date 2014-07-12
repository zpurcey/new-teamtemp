from django.db import models

class WordCloudImage(models.Model):
    creation_date = models.DateField()
    word_list = models.CharField(max_length=511)
    image_url = models.CharField(max_length=255)

class User(models.Model):
    id = models.CharField(max_length=8, primary_key=True)


class TeamTemperature(models.Model):
    id = models.CharField(max_length=8, primary_key=True)
    creation_date = models.DateField()
    creator = models.ForeignKey(User)
    password = models.CharField(max_length=256)

    def stats(self):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(archived = False)
        result['count'] = allresponses.count()
        result['average'] = allresponses.aggregate(models.Avg('score'))
        result['words'] = allresponses.values('word').annotate(models.Count("id")).order_by()
        return result 

    def team_stats(self, team_name):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(team_name = team_name, archived = False)
        result['count'] = allresponses.count()
        result['average'] = allresponses.aggregate(models.Avg('score'))
        result['words'] = allresponses.values('word').annotate(models.Count("id")).order_by()
        return result 

    def archive_stats(self, archive_date):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(archived = True,archive_date = archive_date)
        result['count'] = allresponses.count()
        result['average'] = allresponses.aggregate(models.Avg('score'))
        result['words'] = allresponses.values('word').annotate(models.Count("id")).order_by()
        return result 

    def archive_team_stats(self, team_name, archive_date):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(team_name = team_name, archive_date = archive_date, archived = True)
        result['count'] = allresponses.count()
        result['average'] = allresponses.aggregate(models.Avg('score'))
        result['words'] = allresponses.values('word').annotate(models.Count("id")).order_by()
        return result 

    def accumulated_stats(self, start_date, end_date):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(response_date__gte=end_date, response_date__lte=start_date)
        result['count'] = allresponses.count()
        result['average'] = allresponses.aggregate(models.Avg('score'))
        result['words'] = allresponses.values('word').annotate(models.Count("id")).order_by()
        return result

    def accumulated_team_stats(self, team_name, start_date, end_date):
        result = dict()
        allresponses = self.temperatureresponse_set.filter(team_name = team_name, response_date__gte=end_date, response_date__lte=start_date)
        result['count'] = allresponses.count()
        result['average'] = allresponses.aggregate(models.Avg('score'))
        result['words'] = allresponses.values('word').annotate(models.Count("id")).order_by()
        return result

    def __unicode__(self):
        return u"{}: {} {}".format(self.id, self.creator.id,
                                   self.creation_date)


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
    word_list = models.CharField(max_length=511)
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

    def pretty_team_name(self):
        return self.team_name.replace('_', ' ')

    def __unicode__(self):
        return u"{}: {} {} {} {} {} {} {} {}".format(self.id, self.request.id, 
                                         self.team_name)
