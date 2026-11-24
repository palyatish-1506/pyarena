"""Submission business logic — all scoring/streak rules live here.

Spec §6:
- Correct: base_points (easy 10 / medium 20 / hard 30)
- Speed bonus: +50% of base if answered in first 10% of the open window,
  decaying linearly to 0 at 50% of the window.
- Wrong: 0 points, no negative marking.
- Late (after close_at): 0 points, practice only, still counts for streak.
- Streak: +1 per IST calendar day with >=1 submission; freezes (max 2,
  earned per 7-day streak) auto-consumed on missed days.
"""

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import User
from questions.models import Question

from .models import Submission

LEVELS = [
    (0, "Print Padawan"),
    (100, "Variable Voyager"),
    (300, "Loop Learner"),
    (700, "Function Master"),
    (1500, "Data Wizard"),
    (3000, "Pythonista"),
]

BADGES = {
    "first_answer": "Answered your first question",
    "streak_7": "7-day streak",
    "streak_30": "30-day streak",
    "first_hard_correct": "First hard question correct",
}


def _ist_today():
    """Today's date in Asia/Kolkata (spec: streaks are IST calendar days)."""
    return timezone.localtime(timezone.now(), timezone.get_fixed_timezone(330)).date()


def _level_for(xp: int) -> int:
    level = 1
    for i, (threshold, _) in enumerate(LEVELS):
        if xp >= threshold:
            level = i + 1
    return level


def _speed_bonus(question: Question, now) -> int:
    """Up to +50% of base for answering early in the open window."""
    if not question.release_at:
        return 0
    # Open window = release_at -> close_at (default 24h if no close_at).
    window_end = question.close_at or question.release_at + timedelta(hours=24)
    window = (window_end - question.release_at).total_seconds()
    if window <= 0:
        return 0
    frac = (now - question.release_at).total_seconds() / window
    base = question.base_points
    if frac <= 0.10:
        return int(base * 0.5)
    if frac >= 0.50:
        return 0
    # Linear decay from +50% at 10% to 0 at 50%.
    return int(base * 0.5 * (1 - (frac - 0.10) / 0.40))


def _update_streak(user: User, today) -> int:
    """Advance the IST-day streak, consuming freezes for missed days.
    Returns the new current_streak."""
    last = user.last_active_date
    if last == today:
        return user.current_streak
    if last is None:
        streak = 1
    else:
        gap = (today - last).days
        if gap <= 0:
            streak = user.current_streak or 1
        elif gap == 1:
            streak = user.current_streak + 1
        else:
            missed = gap - 1  # days skipped between last and today
            if missed <= user.streak_freezes:
                user.streak_freezes -= missed
                streak = user.current_streak + 1
            else:
                streak = 1
    user.current_streak = streak
    user.longest_streak = max(user.longest_streak, streak)
    # Earn a freeze per 7-day streak milestone (max 2).
    if streak > 0 and streak % 7 == 0 and user.streak_freezes < 2:
        user.streak_freezes += 1
    user.last_active_date = today
    return streak


def _badges_for(user: User, submission: Submission) -> list[str]:
    earned = []
    if not user.submissions.exclude(pk=submission.pk).exists():
        earned.append("first_answer")
    if submission.is_correct and submission.question.difficulty == Question.Difficulty.HARD:
        if (
            not user.submissions.filter(is_correct=True, question__difficulty="hard")
            .exclude(pk=submission.pk)
            .exists()
        ):
            earned.append("first_hard_correct")
    if user.current_streak == 7:
        earned.append("streak_7")
    if user.current_streak == 30:
        earned.append("streak_30")
    return [b for b in earned if b in BADGES]


class DuplicateSubmission(Exception):
    pass


@transaction.atomic
def submit_answer(
    user: User, question: Question, selected_option_ids: list[int], time_taken_ms: int = 0
) -> dict:
    """Score one attempt. Locks the user row so concurrent submits for the
    same user serialize; UNIQUE(user, question) + IntegrityError -> 409."""
    # Lock the user row — serializes XP/streak updates for this user.
    locked_user = User.objects.select_for_update().get(pk=user.pk)

    now = timezone.now()
    is_late = bool(question.close_at and now > question.close_at)

    correct_ids = set(question.options.filter(is_correct=True).values_list("id", flat=True))
    selected = set(selected_option_ids)
    # Exact-set match: mcq_multi partial selections count as wrong (spec C1).
    is_correct = bool(selected) and selected == correct_ids

    # Late answers are practice-only: correct but 0 points.
    points = 0
    if is_correct and not is_late:
        points = question.base_points + _speed_bonus(question, now)

    try:
        submission = Submission.objects.create(
            user=locked_user,
            question=question,
            selected_option_ids=sorted(selected),
            is_correct=is_correct,
            points_awarded=points,
            time_taken_ms=time_taken_ms,
            is_late=is_late,
        )
    except IntegrityError as exc:
        raise DuplicateSubmission() from exc

    if points:
        locked_user.xp += points
    today = _ist_today()
    streak = _update_streak(locked_user, today)
    new_level = _level_for(locked_user.xp)
    badges = _badges_for(locked_user, submission)
    locked_user.level = new_level
    locked_user.save()

    return {
        "is_correct": submission.is_correct,
        "points_awarded": points,
        "correct_option_ids": sorted(correct_ids),
        "explanation": question.explanation_markdown,
        "new_xp": locked_user.xp,
        "new_level": new_level,
        "level_name": dict((i + 1, name) for i, (_, name) in enumerate(LEVELS))[new_level],
        "streak": streak,
        "badges_earned": badges,
        "is_late": is_late,
    }
