"""Create demo users for local dev / e2e tests.

  senior@demo.pyarena  / DemoSenior!234  (role=senior, approved)
  student@demo.pyarena / DemoStudent!234  (role=student)

Idempotent — safe to run repeatedly. NEVER run in production.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEMO_USERS = [
    {
        "email": "senior@demo.pyarena",
        "password": "DemoSenior!234",
        "full_name": "Demo Senior",
        "role": User.Role.SENIOR,
        "senior_approved": True,
        "division": "A",
    },
    {
        "email": "student@demo.pyarena",
        "password": "DemoStudent!234",
        "full_name": "Demo Student",
        "role": User.Role.STUDENT,
        "division": "A",
    },
]


class Command(BaseCommand):
    help = "Create demo senior + student accounts for local dev and e2e tests."

    def handle(self, *args, **options):
        for data in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=data["email"], defaults={k: v for k, v in data.items() if k != "password"}
            )
            if created:
                user.set_password(data["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"created {user.email} ({user.role})"))
            else:
                # Keep password in sync so e2e stays reproducible.
                user.set_password(data["password"])
                user.role = data["role"]
                user.senior_approved = data.get("senior_approved", False)
                user.save()
                self.stdout.write(f"updated {user.email}")
