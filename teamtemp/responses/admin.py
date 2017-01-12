from django.contrib import admin

from teamtemp.responses.models import *


def _request_id(obj):
    return obj.request.id
_request_id.short_description = 'Request ID'


def _creator_id(obj):
    return obj.creator.id
_creator_id.short_description = 'Creator ID'


def _responder_id(obj):
    return obj.responder.id
_responder_id.short_description = 'Responder ID'


class WordCloudImageAdmin(admin.ModelAdmin):
    list_display = ("id", "word_hash", "image_url", "creation_date")
    list_display_links = ("id", "word_hash", "image_url")
    readonly_fields = ("id", "creation_date", "image_url", "word_list", "word_hash")
    search_fields = ("id", "word_hash", )


class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "creation_date")
    readonly_fields = ("id", "creation_date")
    search_fields = ("id", )


class TeamTemperatureAdmin(admin.ModelAdmin):
    list_display = ("id", _creator_id, "survey_type", "creation_date")
    list_filter = ("survey_type", )
    readonly_fields = ("id", "creation_date", "modified_date")
    raw_id_fields = ("creator", )
    search_fields = ("id", "creator__id")


class TemperatureResponseAdmin(admin.ModelAdmin):
    list_display = ("id", _request_id, _responder_id, "team_name", "score", "word", "response_date")
    list_filter = ("archived", )
    readonly_fields = ("id", )
    raw_id_fields = ("responder", "request")
    search_fields = ("team_name", "request__id")


class TeamResponseHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", _request_id, "team_name", "average_score", "responder_count", "archive_date")
    readonly_fields = ("id", )
    raw_id_fields = ("request", )
    search_fields = ("team_name", "request__id")


class TeamsAdmin(admin.ModelAdmin):
    list_display = ("id", _request_id, "team_name", "dept_name", "site_name", "region_name", "creation_date", "modified_date")
    readonly_fields = ("id", "creation_date", "modified_date")
    raw_id_fields = ("request", )
    search_fields = ("team_name", "request__id")


admin.site.register(WordCloudImage, WordCloudImageAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(TeamTemperature, TeamTemperatureAdmin)
admin.site.register(TemperatureResponse, TemperatureResponseAdmin)
admin.site.register(TeamResponseHistory, TeamResponseHistoryAdmin)
admin.site.register(Teams, TeamsAdmin)
