from django.contrib import admin

from teamtemp.responses.models import *

def _request_id(obj):
    return obj.request.id
_request_id.short_description = 'Request ID'

class WordCloudImageAdmin(admin.ModelAdmin):
    list_display = ("id", "word_hash", "image_url", "creation_date")
    list_display_links = ("id", "word_hash", "image_url")
    readonly_fields = ("id", "creation_date", "image_url", "word_list", "word_hash")


class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "creation_date")
    readonly_fields = ("id", "creation_date")


class TeamTemperatureAdmin(admin.ModelAdmin):
    list_display = ("id", "creator", "survey_type", "creation_date")
    list_filter = ("survey_type", )
    readonly_fields = ("id", "creation_date", "modified_date", "creator")


class TemperatureResponseAdmin(admin.ModelAdmin):
    list_display = ("id", _request_id, "responder", "team_name", "score", "word", "response_date")
    list_filter = ("archived", )
    readonly_fields = ("id", 'responder')


class TeamResponseHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", _request_id, "team_name", "average_score", "responder_count", "archive_date")
    readonly_fields = ("id", )


class TeamsAdmin(admin.ModelAdmin):
    list_display = ("id", _request_id, "team_name", "dept_name", "site_name", "region_name", "creation_date", "modified_date")
    readonly_fields = ("id", "creation_date", "modified_date")


admin.site.register(WordCloudImage, WordCloudImageAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(TeamTemperature, TeamTemperatureAdmin)
admin.site.register(TemperatureResponse, TemperatureResponseAdmin)
admin.site.register(TeamResponseHistory, TeamResponseHistoryAdmin)
admin.site.register(Teams, TeamsAdmin)
