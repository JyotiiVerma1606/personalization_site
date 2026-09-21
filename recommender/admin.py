import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Session, ClickEvent, Rating


def get_name(session_id):
    session = Session.objects.filter(session_id=session_id).first()
    return session.participant_name if session else "—"


@admin.action(description="Selected sessions ka CSV download karo (clicks + ratings)")
def export_selected_sessions_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="selected_participants.csv"'
    writer = csv.writer(response)
    writer.writerow(["name", "session_id", "mode", "item_id", "category", "is_target", "time_taken_ms", "relevance", "ease", "created_at"])

    session_ids = list(queryset.values_list("session_id", flat=True))

    for click in ClickEvent.objects.filter(session_id__in=session_ids).order_by("session_id", "created_at"):
        writer.writerow([
            get_name(click.session_id), click.session_id, click.mode, click.item_id,
            click.category, click.is_target, click.time_taken_ms, "", "", click.created_at
        ])

    for rating in Rating.objects.filter(session_id__in=session_ids).order_by("session_id", "created_at"):
        writer.writerow([
            get_name(rating.session_id), rating.session_id, rating.mode, "", "", "",
            "", rating.relevance, rating.ease, rating.created_at
        ])

    return response


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("participant_name", "session_id", "mode_order", "age_range", "web_familiarity", "created_at")
    search_fields = ("participant_name", "session_id")
    actions = [export_selected_sessions_csv]


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    list_display = ("participant_name", "session_id", "mode", "item_id", "category", "is_target", "time_taken_ms", "created_at")
    list_filter = ("mode", "is_target", "category")
    search_fields = ("session_id",)

    def participant_name(self, obj):
        return get_name(obj.session_id)
    participant_name.short_description = "Name"


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("participant_name", "session_id", "mode", "relevance", "ease", "created_at")
    list_filter = ("mode",)
    search_fields = ("session_id",)

    def participant_name(self, obj):
        return get_name(obj.session_id)
    participant_name.short_description = "Name"