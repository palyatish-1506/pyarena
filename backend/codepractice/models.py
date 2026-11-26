"""Code practice: problems, test cases, submissions."""

from django.conf import settings
from django.db import models


class CodeProblem(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description_markdown = models.TextField()
    starter_code = models.TextField(default="")
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.EASY)
    points = models.PositiveIntegerField(default=100)
    time_limit_ms = models.PositiveIntegerField(default=5000)
    memory_limit_mb = models.PositiveIntegerField(default=128)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title


class TestCase(models.Model):
    problem = models.ForeignKey(CodeProblem, on_delete=models.CASCADE, related_name="test_cases")
    input_data = models.TextField()
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=False)  # hidden tests only run server-side
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.problem.slug} tc{self.order}"


class CodeSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        WRONG_ANSWER = "wrong_answer", "Wrong Answer"
        TIMEOUT = "timeout", "Time Limit"
        RUNTIME_ERROR = "runtime_error", "Runtime Error"
        COMPILE_ERROR = "compile_error", "Compile Error"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="code_submissions"
    )
    problem = models.ForeignKey(CodeProblem, on_delete=models.CASCADE, related_name="submissions")
    code = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    score = models.PositiveIntegerField(default=0)
    is_flagged_similar = models.BooleanField(default=False)
    results = models.JSONField(default=list)  # per-testcase {input, expected, actual, passed}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id}:{self.problem.slug} {self.status}"
