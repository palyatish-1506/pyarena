from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "xp", "level", "is_staff", "is_active")
    list_filter = ("role", "senior_approved", "is_staff", "is_active")
    search_fields = ("email", "full_name", "username", "roll_no")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("username", "full_name", "roll_no", "branch", "year", "division")}),
        ("Role", {"fields": ("role", "senior_approved")}),
        (
            "Gamification",
            {
                "fields": (
                    "xp",
                    "level",
                    "current_streak",
                    "longest_streak",
                    "streak_freezes",
                    "last_active_date",
                    "avatar_seed",
                )
            },
        ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "full_name"),
            },
        ),
    )
