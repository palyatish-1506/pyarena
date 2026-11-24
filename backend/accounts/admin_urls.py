from django.urls import path

from accounts import views
from accounts.admin_exports import users_csv, weekly_results_csv

app_name = "admin_api"

urlpatterns = [
    path("seniors/", views.PendingSeniorsView.as_view(), name="pending-seniors"),
    path("seniors/<int:pk>/approve/", views.ApproveSeniorView.as_view(), name="approve-senior"),
    path("users.csv", users_csv, name="users-csv"),
    path("weekly-results.csv", weekly_results_csv, name="weekly-csv"),
]
