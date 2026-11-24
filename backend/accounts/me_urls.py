from django.urls import path

from gamification import views as gamification_views
from submissions import views as submission_views

from . import views

urlpatterns = [
    path("", views.MeView.as_view(), name="me"),
    path("history/", submission_views.history, name="history"),
    path("topics/", submission_views.topic_progress, name="topic-progress"),
    path("badges/", gamification_views.my_badges, name="badges"),
]
