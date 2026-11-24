from django.urls import path

from . import views

app_name = "questions"

urlpatterns = [
    # Student-facing
    path("today/", views.TodayQuestionsView.as_view(), name="today"),
    path("topics/", views.topics, name="topics"),
    path("<int:pk>/", views.QuestionDetailView.as_view(), name="detail"),
    # Senior-facing
    path("senior/questions/", views.SeniorQuestionListCreate.as_view(), name="senior-list"),
    path("senior/questions/<int:pk>/", views.SeniorQuestionDetail.as_view(), name="senior-detail"),
    path("senior/questions/<int:pk>/duplicate/", views.duplicate, name="senior-duplicate"),
    path("senior/questions/<int:pk>/preview/", views.preview, name="senior-preview"),
]
