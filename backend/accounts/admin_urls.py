from django.urls import path

from accounts import views

app_name = "admin_api"

urlpatterns = [
    path("seniors/", views.PendingSeniorsView.as_view(), name="pending-seniors"),
    path("seniors/<int:pk>/approve/", views.ApproveSeniorView.as_view(), name="approve-senior"),
]
