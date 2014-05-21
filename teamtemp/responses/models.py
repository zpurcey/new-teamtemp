from django.db import models

class User(models.Model):
    id = models.CharField(max_length=8, primary_key=True)


class TeamTemperature(models.Model):
    id = models.CharField(max_length=8, primary_key=True)
    creation_date = models.DateField()
    creator = models.ForeignKey(User)
    password = models.CharField(max_length=256)

    def stats(self, team_name=''):
        result = dict()
        allresponses = self.temperatureresponse_set.all()
        teamresponses = self.temperatureresponse_set.filter(team_name = team_name)
        result['count'] = allresponses.count()
        result['average'] = allresponses.aggregate(models.Avg('score'))
        result['words'] = allresponses.values('word').annotate(models.Count("id")).order_by()
        result['team_count'] = teamresponses.count()
        result['team_average'] = teamresponses.aggregate(models.Avg('score'))
        result['team_words'] = teamresponses.values('word').annotate(models.Count("id")).order_by()
        return result 

    def __unicode__(self):
        return u"{}: {} {}".format(self.id, self.creator.id,
                                   self.creation_date)


class TemperatureResponse(models.Model):
    request = models.ForeignKey(TeamTemperature)
    responder = models.ForeignKey(User)
    score = models.IntegerField()
    word = models.CharField(max_length=32)
    team_name = models.CharField(max_length=32, null=True)

    def __unicode__(self):
        return u"{}: {} {} {} {}".format(self.id, self.request.id, 
                                         self.responder.id,
                                         self.score, self.word, self.team_name)
