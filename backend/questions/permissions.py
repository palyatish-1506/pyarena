"""DRF permissions for role-gated endpoints."""

from rest_framework.permissions import BasePermission

from accounts.models import User


class IsSeniorOrAdmin(BasePermission):
    """Seniors must be admin-approved (senior_approved=True); admins always pass."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role == User.Role.ADMIN:
            return True
        return user.role == User.Role.SENIOR and user.senior_approved
