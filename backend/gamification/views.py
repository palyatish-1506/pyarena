"""Gamification read endpoints."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserBadge


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_badges(request):
    rows = UserBadge.objects.filter(user=request.user).select_related("badge").order_by("-earned_at")
    return Response(
        [
            {
                "badge": {
                    "code": r.badge.code,
                    "name": r.badge.name,
                    "icon": r.badge.icon,
                    "description": r.badge.description,
                },
                "earned_at": r.earned_at,
            }
            for r in rows
        ]
    )
