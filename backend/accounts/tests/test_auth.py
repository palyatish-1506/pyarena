"""Auth endpoint tests — register, login, refresh, logout, /me, reset,
senior request/approve, permissions."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db

BASE = "/api/v1/auth"
ADMIN = "/api/v1/admin"


@pytest.fixture
def client():
    """DRF APIClient (supports .credentials() for Bearer tokens)."""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture(autouse=True)
def _no_throttling(settings):
    """Tests share one IP — disable rate limits so they don't interfere."""
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": "100000/hour",
        "user": "100000/hour",
        "login": "100000/min",
        "register": "100000/hour",
    }


def _register(client, email="student@test.com", password="Str0ng!Pass", **extra):
    payload = {
        "email": email,
        "password": password,
        "password_confirm": password,
        "full_name": "Test Student",
        "roll_no": "CS101",
    }
    payload.update(extra)
    return client.post(f"{BASE}/register/", payload, format="json")


def _login(client, email="student@test.com", password="Str0ng!Pass"):
    return client.post(f"{BASE}/login/", {"email": email, "password": password}, format="json")


def _auth_client(client, email="student@test.com", password="Str0ng!Pass"):
    """Login and return (client, access_token)."""
    res = _login(client, email, password)
    assert res.status_code == 200
    token = res.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client, token


# ---------- register / login / tokens ----------


def test_register_returns_access_in_body_and_refresh_cookie(client):
    res = _register(client)
    assert res.status_code == 201
    assert res.json()["user"]["email"] == "student@test.com"
    assert res.json()["user"]["role"] == "student"  # role forced
    assert "access" in res.json()
    assert "access_token" not in res.cookies  # access NOT in cookie anymore
    assert "refresh_token" in res.cookies  # refresh IS httpOnly cookie
    assert User.objects.get(email="student@test.com").check_password("Str0ng!Pass")


def test_register_rejects_duplicate_email(client):
    _register(client)
    res = _register(client)
    assert res.status_code == 400
    assert "email" in res.json()


def test_register_rejects_password_mismatch(client):
    res = client.post(
        f"{BASE}/register/",
        {"email": "a@b.com", "password": "Str0ng!Pass", "password_confirm": "nope"},
        format="json",
    )
    assert res.status_code == 400


def test_register_validates_roll_no_format(client):
    res = _register(client, email="r@t.dev", roll_no="!!!bad!!!")
    assert res.status_code == 400
    assert "roll_no" in res.json()


def test_login_returns_access_and_me_works_with_bearer(client):
    _register(client)
    res = _login(client)
    assert res.status_code == 200
    token = res.json()["access"]
    assert token

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    me = client.get("/api/v1/me/")
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "student@test.com"


def test_me_rejects_anonymous(client):
    assert client.get("/api/v1/me/").status_code in (401, 403)


def test_me_patch_updates_profile(client):
    _register(client)
    client, _ = _auth_client(client)
    res = client.patch("/api/v1/me/", {"full_name": "New Name", "division": "B"}, format="json")
    assert res.status_code == 200
    assert res.json()["user"]["full_name"] == "New Name"
    assert res.json()["user"]["division"] == "B"


# ---------- refresh / logout / blacklist ----------


def test_refresh_returns_new_access_and_rotates_refresh_cookie(client):
    _register(client)
    login = _login(client)
    old_refresh = login.cookies["refresh_token"].value

    res = client.post(f"{BASE}/refresh/")
    assert res.status_code == 200
    assert "access" in res.json()
    assert res.cookies["refresh_token"].value != old_refresh  # rotated


def test_logout_blacklists_refresh_token(client):
    _register(client)
    _login(client)
    res = client.post(f"{BASE}/logout/")
    assert res.status_code == 200
    # Reusing the blacklisted refresh token must fail.
    res2 = client.post(f"{BASE}/refresh/")
    assert res2.status_code == 401


# ---------- password reset ----------


def test_password_reset_flow(client, outbox=None):
    _register(client)
    res = client.post(f"{BASE}/password-reset/", {"email": "student@test.com"}, format="json")
    assert res.status_code == 200
    # unknown email also returns 200 (no enumeration)
    res2 = client.post(f"{BASE}/password-reset/", {"email": "nobody@x.dev"}, format="json")
    assert res2.status_code == 200


def test_password_reset_confirm_with_token(client):
    from django.contrib.auth.tokens import PasswordResetTokenGenerator
    from django.utils.encoding import force_bytes
    from django.utils.http import urlsafe_base64_encode

    _register(client)
    user = User.objects.get(email="student@test.com")
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    res = client.post(
        f"{BASE}/password-reset/confirm/",
        {"uid": uid, "token": token, "new_password": "N3w!Passw0rd"},
        format="json",
    )
    assert res.status_code == 200
    assert _login(client, password="N3w!Passw0rd").status_code == 200


# ---------- senior request / approve ----------


def test_student_requests_senior_and_admin_approves(client):
    _register(client)
    client, _ = _auth_client(client)
    res = client.post(f"{BASE}/request-senior/")
    assert res.status_code == 200
    assert res.json()["user"]["senior_requested"] is True

    # Non-admin cannot approve.
    res = client.post(f"{ADMIN}/seniors/1/approve/")
    assert res.status_code == 403

    # Admin approves.
    admin = User.objects.create_user(email="adm@t.dev", password="x", role=User.Role.ADMIN)
    admin_client = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken

    admin_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(admin).access_token}")
    pending = admin_client.get(f"{ADMIN}/seniors/")
    assert pending.status_code == 200
    uid = pending.json()[0]["id"] if isinstance(pending.json(), list) else pending.json()["results"][0]["id"]
    res = admin_client.post(f"{ADMIN}/seniors/{uid}/approve/")
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "senior"
    assert res.json()["user"]["senior_approved"] is True


# ---------- permissions C3 ----------


def test_student_cannot_access_senior_or_admin_endpoints(client):
    _register(client)
    client, _ = _auth_client(client)
    assert client.get("/api/v1/questions/senior/questions/").status_code == 403
    assert client.get(f"{ADMIN}/seniors/").status_code == 403


def test_anonymous_cannot_access_protected(client):
    assert client.get("/api/v1/questions/today/").status_code in (401, 403)
