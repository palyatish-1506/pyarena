from django.urls import path

from . import views

urlpatterns = [
    path("create/", views.create, name="create"),
    path("mine/", views.my_quizzes, name="mine"),
    path("<str:code>/", views.info, name="info"),
]
