from django.urls import path

from . import views

urlpatterns = [
    path("questions/<int:pk>/comments/", views.comments, name="comments"),
    path("comments/<int:comment_id>/upvote/", views.upvote, name="upvote"),
    path("comments/<int:comment_id>/accept/", views.accept, name="accept"),
    path("comments/<int:comment_id>/report/", views.report, name="report"),
]
