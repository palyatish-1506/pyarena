"""Leaderboard business logic.

Scoring source: submissions.points_awarded summed per user.
Windows: weekly = Mon 00:00 IST -> now; season = active Season or all-time.
Ranks use SQL window functions (Django Window + Rank) — one query, no N+1.
Responses cached 60s per spec; the "me" block is computed per-user (never cached).
"""

from datetime import UTC, timedelta

from django.core.cache import cache
from django.db.models import Count, F, Sum, Window
from django.db.models.functions import Rank
from django.utils import timezone

from accounts.models import User
from gamification.models import Season
from submissions.models import Submission

CACHE_TTL = 60
PAGE_SIZE = 50
IST = timezone.get_fixed_timezone(330)  # Asia/Kolkata UTC+5:30


def week_bounds(now=None):
    """Return (this_week_start_utc, last_week_start_utc) — Monday 00:00 IST."""
    now = now or timezone.now()
    ist = now.astimezone(IST)
    monday = ist.date() - timedelta(days=ist.weekday())

    def _utc(y, m, d):
        return timezone.make_aware(timezone.datetime(y, m, d), IST).astimezone(UTC)

    this_start = _utc(monday.year, monday.month, monday.day)
    last_start = this_start - timedelta(days=7)
    return this_start, last_start


def _score_queryset(qs):
    """Annotate per-user score + RANK() in a single SQL query."""
    return (
        qs.values("user_id")
        .annotate(score=Sum("points_awarded"))
        .annotate(rank=Window(expression=Rank(), order_by=F("score").desc()))
        .order_by("rank")
    )


def _hydrate(rows, limit=None, offset=0):
    """Attach user display fields to ranked rows (single IN query — no N+1)."""
    rows = list(rows[offset : offset + (limit or len(rows))]) if offset or limit else list(rows)
    ids = [r["user_id"] for r in rows]
    users = {u.id: u for u in User.objects.filter(id__in=ids)}
    out = []
    for r in rows:
        u = users.get(r["user_id"])
        out.append(
            {
                "rank": r["rank"],
                "score": r["score"],
                "user_id": r["user_id"],
                "email": u.email if u else "?",
                "full_name": u.full_name if u else "?",
                "avatar_seed": u.avatar_seed if u else "",
                "level": u.level if u else 1,
                "division": u.division if u else "",
            }
        )
    return out


def _weekly_qs(extra_filter=None):
    start, _ = week_bounds()
    qs = Submission.objects.filter(submitted_at__gte=start)
    if extra_filter:
        qs = qs.filter(**extra_filter)
    return qs


def _compute_rows(scope: str, division: str | None, page: int) -> list[dict]:
    offset = (page - 1) * PAGE_SIZE
    end = offset + PAGE_SIZE

    if scope == "season":
        season = Season.objects.filter(is_active=True).first()
        if season:
            s = timezone.make_aware(
                timezone.datetime.combine(season.start_date, timezone.datetime.min.time()), IST
            )
            e = timezone.make_aware(
                timezone.datetime.combine(season.end_date + timedelta(days=1), timezone.datetime.min.time()),
                IST,
            )
            qs = Submission.objects.filter(submitted_at__gte=s, submitted_at__lt=e)
        else:
            qs = Submission.objects.all()
        return _hydrate(_score_queryset(qs)[:end], limit=PAGE_SIZE, offset=offset)

    if scope == "division_battle":
        # Avg weekly points per ACTIVE member of each division.
        start, _ = week_bounds()
        rows = (
            Submission.objects.filter(submitted_at__gte=start)
            .values("user__division")
            .annotate(
                total=Sum("points_awarded"),
                members=Count("user", distinct=True),
            )
            .order_by("-total")
        )
        return [
            {
                "division": r["user__division"] or "?",
                "total_points": r["total"],
                "active_members": r["members"],
                "avg_per_member": round(r["total"] / r["members"], 1) if r["members"] else 0,
            }
            for r in rows
        ]

    if scope == "improved":
        this_start, last_start = week_bounds()
        this_qs = Submission.objects.filter(submitted_at__gte=this_start)
        last_qs = Submission.objects.filter(submitted_at__gte=last_start, submitted_at__lt=this_start)
        this_scores = {r["user_id"]: r["score"] for r in _score_queryset(this_qs).values("user_id", "score")}
        last_scores = {r["user_id"]: r["score"] for r in _score_queryset(last_qs).values("user_id", "score")}
        improved = [
            {
                "user_id": uid,
                "score": this_scores.get(uid, 0) - last_scores.get(uid, 0),
                "this_week": this_scores.get(uid, 0),
                "last_week": last_scores.get(uid, 0),
            }
            for uid in set(this_scores) | set(last_scores)
            if this_scores.get(uid, 0) - last_scores.get(uid, 0) > 0
        ]
        improved.sort(key=lambda r: -r["score"])
        # Attach rank manually (small set, correctness over micro-perf).
        for i, r in enumerate(improved):
            r["rank"] = i + 1
        return _hydrate(improved[offset:end])

    # weekly | division | beginner — all weekly windows with optional filters.
    if scope == "division":
        if not division:
            return []
        user_ids = User.objects.filter(division__iexact=division).values_list("id", flat=True)
        qs = _weekly_qs().filter(user_id__in=user_ids)
    elif scope == "beginner":
        user_ids = User.objects.filter(level__lt=3).values_list("id", flat=True)
        qs = _weekly_qs().filter(user_id__in=user_ids)
    else:  # weekly
        qs = _weekly_qs()
    return _hydrate(_score_queryset(qs)[:end], limit=PAGE_SIZE, offset=offset)


def _me_block(scope: str, division: str | None, user: User | None) -> dict | None:
    if not user or not user.is_authenticated:
        return None
    uid = user.id

    def _rank_and_next(qs):
        ranked = list(_score_queryset(qs))
        mine = next((r for r in ranked if r["user_id"] == uid), None)
        if not mine:
            return {"rank": None, "score": 0, "gap_to_next": None}
        idx = ranked.index(mine)
        nxt = ranked[idx - 1] if idx > 0 else None
        return {
            "rank": mine["rank"],
            "score": mine["score"],
            "gap_to_next": (nxt["score"] - mine["score"]) if nxt else 0,
        }

    if scope == "season":
        season = Season.objects.filter(is_active=True).first()
        if season:
            s = timezone.make_aware(
                timezone.datetime.combine(season.start_date, timezone.datetime.min.time()), IST
            )
            e = timezone.make_aware(
                timezone.datetime.combine(season.end_date + timedelta(days=1), timezone.datetime.min.time()),
                IST,
            )
            qs = Submission.objects.filter(submitted_at__gte=s, submitted_at__lt=e)
        else:
            qs = Submission.objects.all()
        return _rank_and_next(qs)

    if scope == "division_battle":
        return None  # per-division aggregate, no personal rank

    if scope == "improved":
        # Reuse the same computation but only need the user's delta.
        this_start, last_start = week_bounds()
        this_q = (
            _score_queryset(Submission.objects.filter(submitted_at__gte=this_start))
            .filter(user_id=uid)
            .values("score")
        )
        last_q = (
            _score_queryset(
                Submission.objects.filter(submitted_at__gte=last_start, submitted_at__lt=this_start)
            )
            .filter(user_id=uid)
            .values("score")
        )
        this_score = this_q.first()["score"] if this_q.exists() else 0
        last_score = last_q.first()["score"] if last_q.exists() else 0
        delta = this_score - last_score
        return {
            "rank": None,
            "score": delta,
            "gap_to_next": None,
            "this_week": this_score,
            "last_week": last_score,
        }

    qs = _weekly_qs()
    if scope == "division" and division:
        uids = User.objects.filter(division__iexact=division).values_list("id", flat=True)
        qs = qs.filter(user_id__in=uids)
    elif scope == "beginner":
        uids = User.objects.filter(level__lt=3).values_list("id", flat=True)
        qs = qs.filter(user_id__in=uids)
    return _rank_and_next(qs)


def leaderboard(scope: str, division: str | None, user, page: int) -> dict:
    key = f"lb:{scope}:{division or ''}:{page}"
    rows = cache.get(key)
    if rows is None:
        rows = _compute_rows(scope, division, page)
        cache.set(key, rows, CACHE_TTL)
    return {
        "scope": scope,
        "division": division,
        "page": page,
        "rows": rows,
        "me": _me_block(scope, division, user),
    }
