"""Role permissions for question endpoints — canonical classes live in
accounts.permissions; kept here for backwards-compatible imports."""

from accounts.permissions import IsAdmin, IsApprovedSenior, IsStudent

IsSeniorOrAdmin = IsApprovedSenior  # legacy alias

__all__ = ["IsAdmin", "IsApprovedSenior", "IsStudent", "IsSeniorOrAdmin"]
