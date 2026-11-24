"""Business logic for accounts. Views stay thin; rules live here."""

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


@transaction.atomic
def register_user(*, email: str, password: str, full_name: str = "", **profile_fields) -> User:
    """Create a student account. Senior/admin roles are never self-assignable —
    seniors must be approved by an admin (spec §2), so role is forced to
    STUDENT here regardless of input.
    """
    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        role=User.Role.STUDENT,
        **profile_fields,
    )
    return user
