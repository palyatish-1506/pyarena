"""Badge engine — rules from spec §6, evaluated after submissions/comments.

Idempotent: UserBadge UNIQUE(user,badge) + get_or_create means re-running
evaluation never double-awards. Called from submissions.services and
community.services — never directly from views.
"""

from datetime import time as dt_time
from datetime import timedelta

from django.utils import timezone

from accounts.models import User
from submissions.models import Submission

from .models import Badge, UserBadge

IST = timezone.get_fixed_timezone(330)

DEFAULT_BADGES = [
    ("first_answer", "First Answer", "Answered your first question", "🎯"),
    ("streak_7", "7-Day Streak", "Answered for 7 days straight", "🔥"),
    ("streak_30", "30-Day Streak", "A full month of daily answers", "🌟"),
    ("first_hard_correct", "Hard Solver", "First hard question correct", "🧠"),
    ("perfect_week", "Perfect Week", "7 days active in one week", "💯"),
    ("night_owl", "Night Owl", "Answered between 23:00–04:00 IST", "🦉"),
    ("helper_10", "Community Helper", "10 upvoted comments", "🤝"),
    ("top10_weekly", "Weekly Top 10", "Reached top 10 on weekly board", "🏆"),
]


def ensure_badges() -> None:
    """Create the catalog rows if missing (idempotent)."""
    for code, name, desc, icon in DEFAULT_BADGES:
        Badge.objects.get_or_create(code=code, defaults={"name": name, "description": desc, "icon": icon})


def _award(user: User, code: str) -> str | None:
    badge = Badge.objects.filter(code=code).first()
    if not badge:
        return None
    _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
    return code if created else None


def evaluate_after_submission(user: User, submission: Submission) -> list[str]:
    """Check every rule that can be affected by a new submission."""
    earned = []
    ensure_badges()

    subs = Submission.objects.filter(user=user)
    if subs.count() == 1:
        earned += [c for c in [_award(user, "first_answer")] if c]

    if user.current_streak >= 7:
        earned += [c for c in [_award(user, "streak_7")] if c]
    if user.current_streak >= 30:
        earned += [c for c in [_award(user, "streak_30")] if c]

    if (
        submission.is_correct
        and submission.question.difficulty == "hard"
        and not subs.filter(is_correct=True, question__difficulty="hard").exclude(pk=submission.pk).exists()
    ):
        earned += [c for c in [_award(user, "first_hard_correct")] if c]

    # night_owl: submission made 23:00–04:00 IST.
    ist_time = submission.submitted_at.astimezone(IST).time()
    if ist_time >= dt_time(23, 0) or ist_time < dt_time(4, 0):
        earned += [c for c in [_award(user, "night_owl")] if c]

    # perfect_week: 7 distinct IST days in the last 7 days.
    days = {
        s.submitted_at.astimezone(IST).date()
        for s in subs.filter(submitted_at__gte=timezone.now() - timedelta(days=7))
    }
    if len(days) >= 7:
        earned += [c for c in [_award(user, "perfect_week")] if c]

    # top10_weekly: rank <= 10 on the current weekly board.
    from leaderboard.services import _score_queryset, _weekly_qs

    ranked = list(_score_queryset(_weekly_qs()).values("user_id", "score", "rank"))
    mine = next((r for r in ranked if r["user_id"] == user.id), None)
    if mine and mine["rank"] <= 10:
        earned += [c for c in [_award(user, "top10_weekly")] if c]

    return earned


def evaluate_after_comment(user: User) -> list[str]:
    """helper_10: 10 comments with >=1 upvote... spec says '10 upvoted
    comments' — we count comments that received at least one upvote."""
    ensure_badges()
    from community.models import Comment

    upvoted = Comment.objects.filter(user=user, upvotes__gte=1).count()
    if upvoted >= 10:
        return [c for c in [_award(user, "helper_10")] if c]
    return []
