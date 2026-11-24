"""Live quiz models — host creates a room from questions; players join by code."""

import secrets

from django.conf import settings
from django.db import models

from questions.models import Question


class LiveQuiz(models.Model):
    class Status(models.TextChoices):
        LOBBY = "lobby", "Lobby"
        LIVE = "live", "Live"
        REVEAL = "reveal", "Reveal"
        FINISHED = "finished", "Finished"

    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="live_quizzes")
    code = models.CharField(max_length=6, unique=True, db_index=True)
    title = models.CharField(max_length=120, default="Live Quiz")
    questions = models.ManyToManyField(Question, related_name="live_quizzes")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.LOBBY)
    current_index = models.PositiveSmallIntegerField(default=0)
    question_time_limit = models.PositiveSmallIntegerField(default=20)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} ({self.status})"

    @classmethod
    def create(cls, host, title, questions, time_limit=20):
        while True:
            code = "".join(secrets.choice("ABCDEFGHJKMNPQRSTUVWXYZ23456789") for _ in range(6))
            if not cls.objects.filter(code=code).exists():
                break
        quiz = cls.objects.create(host=host, code=code, title=title, question_time_limit=time_limit)
        quiz.questions.set(questions)
        return quiz


class LiveQuizParticipant(models.Model):
    quiz = models.ForeignKey(LiveQuiz, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="live_participations"
    )
    score = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveSmallIntegerField(default=0)
    answered_count = models.PositiveSmallIntegerField(default=0)
    last_answer_ms = models.PositiveIntegerField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["quiz", "user"], name="unique_quiz_participant")]

    def __str__(self):
        return f"{self.user_id}@{self.quiz.code} ({self.score})"


class LiveQuizAnswer(models.Model):
    """One answer per participant per question — first answer wins."""

    quiz = models.ForeignKey(LiveQuiz, on_delete=models.CASCADE, related_name="answers")
    participant = models.ForeignKey(LiveQuizParticipant, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option_ids = models.JSONField(default=list)
    time_taken_ms = models.PositiveIntegerField(default=0)
    is_correct = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participant", "question"], name="unique_live_answer_per_question"
            )
        ]

    def __str__(self):
        return f"{self.participant_id}:q{self.question_id} {'✓' if self.is_correct else '✗'}"
