from django.urls import path

from . import views

urlpatterns = [
    path("", views.problems, name="problems"),
    path("<slug:slug>/", views.problem_detail, name="detail"),
    path("<slug:slug>/submit/", views.submit, name="submit"),
    path("<slug:slug>/submissions/", views.my_submissions, name="subs"),
]
