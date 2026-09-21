from django.db import models


class Session(models.Model):
    session_id = models.CharField(max_length=50, unique=True)
    participant_name = models.CharField(max_length=100, blank=True)   # <-- naya
    mode_order = models.CharField(max_length=100)
    age_range = models.CharField(max_length=20, blank=True)
    web_familiarity = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ClickEvent(models.Model):
    session_id = models.CharField(max_length=50)
    mode = models.CharField(max_length=20)
    item_id = models.IntegerField()
    category = models.CharField(max_length=50)
    is_target = models.BooleanField(default=False)
    time_taken_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Rating(models.Model):
    session_id = models.CharField(max_length=50)
    mode = models.CharField(max_length=20)
    relevance = models.IntegerField()
    ease = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)