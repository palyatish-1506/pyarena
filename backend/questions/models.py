"""Question-authoring models: Topic, Question, Option (spec §5)."""

from django.conf import settings
from django.db import models


class Topic(models.Model):
    """A Python topic questions are filed under (Basics, Loops, OOP...)."""

    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Question(models.Model):
    """A poll-style question authored by a senior (or admin).

    Lifecycle: draft -> scheduled -> published -> archived.
    Students only ever see published questions whose release_at has passed —
    enforced in services.visible_to_students(), never by a background job.
    """

    class Type(models.TextChoices):
        MCQ_SINGLE = "mcq_single", "Single choice"
        MCQ_MULTI = "mcq_multi", "Multiple choice"
        OUTPUT = "output", "Predict the output"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    BASE_POINTS = {Difficulty.EASY: 10, Difficulty.MEDIUM: 20, Difficulty.HARD: 30}

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name="questions")
    type = models.CharField(max_length=12, choices=Type.choices)
    title = models.CharField(max_length=200)
    body_markdown = models.TextField()
    code_snippet = models.TextField(blank=True)
    difficulty = models.CharField(max_length=6, choices=Difficulty.choices)
    explanation_markdown = models.TextField(blank=True)
    base_points = models.PositiveSmallIntegerField(default=10)
    release_at = models.DateTimeField(null=True, blank=True)
    close_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # "What's live right now?" — the student feed query.
            models.Index(fields=["status", "release_at"]),
            # Browse/filter questions by topic + difficulty.
            models.Index(fields=["topic", "difficulty"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Option(models.Model):
    """One answer choice. is_correct is NEVER serialized to students
    before they submit (enforced by the student serializer, not here)."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["question", "order"], name="unique_option_order_per_question")
        ]

    def __str__(self):
        return f"{self.question_id}:{self.order} {self.text[:40]}"
