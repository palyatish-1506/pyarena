"""Role-based DRF permission classes (spec: IsStudent, IsApprovedSenior, IsAdmin)."""

from rest_framework.permissions import BasePermission

from .models import User


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.STUDENT)


class IsApprovedSenior(BasePermission):
    """Senior role AND admin-approved (senior_approved=True)."""

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and (u.role == User.Role.ADMIN or (u.role == User.Role.SENIOR and u.senior_approved))
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN)
