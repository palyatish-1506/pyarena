"""Leaderboard endpoints."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .services import leaderboard

SCOPES = {"weekly", "division", "division_battle", "improved", "beginner", "season"}


@api_view(["GET"])
@permission_classes([AllowAny])
def index(request):
    scope = request.query_params.get("scope", "weekly")
    if scope not in SCOPES:
        return Response({"detail": f"scope must be one of {sorted(SCOPES)}"}, status=400)
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except ValueError:
        page = 1
    division = request.query_params.get("division") or None
    return Response(leaderboard(scope, division, request.user, page))
