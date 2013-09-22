from django.db import models

class User(models.Model):
    id = models.CharField(max_length=8, primary_key=True)


class TeamTemperature(models.Model):
    id = models.CharField(max_length=8, primary_key=True)
    creation_date = models.DateField()
    duration = models.IntegerField()
    creator_id = models.ForeignKey(User)
    password = models.CharField(max_length=256)

    def stats(self):
        result = dict()
        responses = self.temperatureresponse_set.all()
        result['count'] = responses.count()
        result['average'] = responses.aggregate(models.Avg('score'))
        result['words'] = responses.values('word').annotate(models.Count("id")).order_by()
        return result 


class TemperatureResponse(models.Model):
    request_id = models.ForeignKey(TeamTemperature)
    responder_id = models.ForeignKey(User)
    score = models.IntegerField()
    word = models.CharField(max_length=32)
