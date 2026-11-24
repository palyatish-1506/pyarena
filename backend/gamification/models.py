"""Badge catalog + user badge awards + seasons (spec §5/§6/§7)."""

from django.conf import settings
from django.db import models


class Badge(models.Model):
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=20, default="🏅")

    def __str__(self):
        return f"{self.icon} {self.name}"


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awards")
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "badge"], name="unique_user_badge")]

    def __str__(self):
        return f"{self.user_id}:{self.badge.code}"


class Season(models.Model):
    name = models.CharField(max_length=80)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"
