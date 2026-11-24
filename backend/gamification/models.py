"""Season model — leaderboard seasons with admin-controlled start/end."""

from django.db import models


class Season(models.Model):
    name = models.CharField(max_length=80)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"
