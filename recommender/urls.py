from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/session/start", views.api_session_start, name="api_session_start"),
    path("api/items", views.api_items, name="api_items"),
    path("api/items/random", views.api_items_random, name="api_items_random"),
    path("api/recommendations", views.api_recommendations, name="api_recommendations"),
    path("api/click", views.api_click, name="api_click"),
    path("api/rating", views.api_rating, name="api_rating"),
    path("api/log", views.api_log, name="api_log"),
    path("api/ratings", views.api_ratings_log, name="api_ratings_log"),
    path("export/clicks.csv", views.export_clicks_csv, name="export_clicks_csv"),
    path("export/ratings.csv", views.export_ratings_csv, name="export_ratings_csv"),
]