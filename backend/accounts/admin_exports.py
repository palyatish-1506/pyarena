"""Admin CSV exports — staff-only."""

import csv

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

from leaderboard.services import week_bounds
from submissions.models import Submission

User = get_user_model()


def _csv_response(filename, header, rows):
    res = HttpResponse(content_type="text/csv")
    res["Content-Disposition"] = f'attachment; filename="{filename}"'
    w = csv.writer(res)
    w.writerow(header)
    w.writerows(rows)
    return res


@api_view(["GET"])
@permission_classes([IsAdminUser])
def users_csv(request):
    rows = User.objects.values_list(
        "id",
        "email",
        "full_name",
        "roll_no",
        "division",
        "role",
        "senior_approved",
        "xp",
        "level",
        "date_joined",
    )
    return _csv_response(
        f"users-{timezone.now():%Y%m%d}.csv",
        [
            "id",
            "email",
            "full_name",
            "roll_no",
            "division",
            "role",
            "senior_approved",
            "xp",
            "level",
            "date_joined",
        ],
        rows,
    )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def weekly_results_csv(request):
    start, _ = week_bounds()
    subs = (
        Submission.objects.filter(submitted_at__gte=start)
        .select_related("user")
        .order_by("-points_awarded", "-submitted_at")
    )
    rows = [
        [
            s.user.email,
            s.user.full_name,
            s.user.division,
            s.question_id,
            s.is_correct,
            s.points_awarded,
            s.is_late,
            s.time_taken_ms,
            s.submitted_at.isoformat(),
        ]
        for s in subs
    ]
    return _csv_response(
        f"weekly-results-{timezone.now():%Y%m%d}.csv",
        ["email", "name", "division", "question_id", "correct", "points", "late", "time_ms", "submitted_at"],
        rows,
    )
