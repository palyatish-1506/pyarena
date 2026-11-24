"""Business rules for questions — views stay thin, logic lives here."""

import random

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from .models import Option, Question


def validate_options(question_type: str, options: list[dict]) -> None:
    """Spec rules: MCQ needs 2-6 options and >=1 correct;
    mcq_single must have exactly one correct answer."""
    from django.core.exceptions import ValidationError

    if not 2 <= len(options) <= 6:
        raise ValidationError("A question needs between 2 and 6 options.")
    correct = [o for o in options if o.get("is_correct")]
    if not correct:
        raise ValidationError("At least one option must be marked correct.")
    if question_type == Question.Type.MCQ_SINGLE and len(correct) != 1:
        raise ValidationError("Single-choice questions must have exactly one correct option.")


def _apply_status_timing(question: Question) -> None:
    """Derive status from the schedule: no release_at -> draft (unscheduled),
    release_at in future -> scheduled, release_at passed -> published.
    Explicit 'archived' is never overridden here."""
    if question.status == Question.Status.ARCHIVED:
        return
    now = timezone.now()
    if question.release_at is None:
        question.status = Question.Status.DRAFT
    elif question.release_at > now:
        question.status = Question.Status.SCHEDULED
    else:
        question.status = Question.Status.PUBLISHED


@transaction.atomic
def create_question(
    *,
    author,
    topic,
    type,
    title,
    body_markdown,
    options,
    difficulty,
    code_snippet="",
    explanation_markdown="",
    release_at=None,
    close_at=None,
    status=Question.Status.DRAFT,
) -> Question:
    """Create a question with its options. Validates option rules and
    derives base_points from difficulty when not supplied."""
    validate_options(type, options)

    question = Question.objects.create(
        author=author,
        topic=topic,
        type=type,
        title=title,
        body_markdown=body_markdown,
        code_snippet=code_snippet,
        difficulty=difficulty,
        explanation_markdown=explanation_markdown,
        base_points=Question.BASE_POINTS[difficulty],
        release_at=release_at,
        close_at=close_at,
        status=status,
    )
    Option.objects.bulk_create(
        [
            Option(
                question=question,
                text=o["text"],
                is_correct=o.get("is_correct", False),
                order=o.get("order", i),
            )
            for i, o in enumerate(options)
        ]
    )
    _apply_status_timing(question)
    question.save(update_fields=["status"])
    return question


@transaction.atomic
def duplicate_question(question: Question, *, author) -> Question:
    """Copy a question (with options) as a new draft owned by `author`."""
    copy = Question.objects.create(
        author=author,
        topic=question.topic,
        type=question.type,
        title=f"{question.title} (copy)",
        body_markdown=question.body_markdown,
        code_snippet=question.code_snippet,
        difficulty=question.difficulty,
        explanation_markdown=question.explanation_markdown,
        base_points=question.base_points,
        status=Question.Status.DRAFT,
    )
    Option.objects.bulk_create(
        [
            Option(
                question=copy,
                text=o.text,
                is_correct=o.is_correct,
                order=o.order,
            )
            for o in question.options.all()
        ]
    )
    return copy


def visible_to_students(now=None) -> QuerySet:
    """The ONLY queryset students may see.

    A question is visible when it is published OR scheduled-with-release-passed
    (scheduled questions auto-"publish" the moment release_at <= now — no
    background job needed, visibility is computed at query time)."""
    now = now or timezone.now()
    return (
        Question.objects.filter(
            status__in=[Question.Status.PUBLISHED, Question.Status.SCHEDULED],
            release_at__lte=now,
        )
        .select_related("topic")
        .prefetch_related("options")
    )


def shuffled_options(question: Question, user_id: int) -> list[Option]:
    """Deterministic per-user shuffle (spec §6): same user always sees the
    same order for a given question; different users see different orders.
    Seed = user_id + question_id."""
    options = list(question.options.all())
    random.Random(user_id + question.id).shuffle(options)
    return options
