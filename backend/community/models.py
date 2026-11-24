"""Comment model — doubt-solving thread under questions (community app)."""

from django.conf import settings
from django.db import models

from questions.models import Question


class Comment(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    body = models.TextField()
    upvotes = models.PositiveIntegerField(default=0)
    is_accepted = models.BooleanField(default=False)  # senior "accepted answer"
    is_hidden = models.BooleanField(default=False)  # admin moderation
    report_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["question", "is_hidden"])]

    def __str__(self):
        return f"comment {self.id} on q{self.question_id} by {self.user_id}"
