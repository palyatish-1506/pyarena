"""Small project-level API views that don't belong to a single app."""

from django.db import connection
from django.http import JsonResponse


def health(request):
    """GET /api/v1/health/ -> {"status": "ok", "db": "ok" | "error"}.

    Also proves the request path browser -> Django -> PostgreSQL works.
    """
    db_status = "ok"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_status = "error"
    status = "ok" if db_status == "ok" else "degraded"
    return JsonResponse({"status": status, "db": db_status})


def debug_sentry(request):
    """GET /api/v1/debug-sentry/ -> deliberately raises to verify Sentry.

    Staff-only; remove after C3 verification.
    """
    if not request.user.is_staff:
        return JsonResponse({"detail": "staff only"}, status=403)
    raise RuntimeError("Sentry test error — safe to ignore")
