"""Submission model — one attempt per (user, question), enforced by DB."""

from django.conf import settings
from django.db import models

from questions.models import Question


class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="submissions")
    selected_option_ids = models.JSONField(default=list)
    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveSmallIntegerField(default=0)
    time_taken_ms = models.PositiveIntegerField(default=0)
    is_late = models.BooleanField(default=False)  # after close_at -> practice only
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "question"], name="unique_submission_per_user_question")
        ]
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["user", "-submitted_at"]),
            # Leaderboard aggregation scans by time window + user.
            models.Index(fields=["submitted_at", "user"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.question_id} {'✓' if self.is_correct else '✗'}"
