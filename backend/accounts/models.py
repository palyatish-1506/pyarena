from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager for our custom User — creates users by email, not username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model — email is the login identifier.

    Defined before the first migration; AUTH_USER_MODEL = "accounts.User".
    Roles: student (default) answers quizzes; senior (approved by admin)
    creates questions; admin manages everything. Gamification fields
    (xp/level/streaks) are written by the gamification app later.
    """

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        SENIOR = "senior", "Senior"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=120, blank=True)
    roll_no = models.CharField(max_length=20, unique=True, null=True, blank=True)
    branch = models.CharField(max_length=80, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    division = models.CharField(max_length=10, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    senior_approved = models.BooleanField(default=False)
    senior_requested = models.BooleanField(default=False)

    # Gamification (written by services in later milestones)
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveSmallIntegerField(default=1)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    streak_freezes = models.PositiveSmallIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    avatar_seed = models.CharField(max_length=40, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self):
        return self.full_name or self.email
