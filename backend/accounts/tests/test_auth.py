"""Auth endpoint tests — register, login, refresh, logout, /me."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db

BASE = "/api/v1/auth"


def _register(client, email="student@test.com", password="Str0ng!Pass"):
    return client.post(
        f"{BASE}/register/",
        {
            "email": email,
            "password": password,
            "password_confirm": password,
            "full_name": "Test Student",
            "roll_no": "CS101",
        },
        format="json",
    )


def test_register_creates_user_and_sets_cookies(client):
    res = _register(client)
    assert res.status_code == 201
    assert res.json()["email"] == "student@test.com"
    # Role is forced to student even though we didn't ask for one.
    assert res.json()["role"] == "student"
    assert "access_token" in res.cookies
    assert "refresh_token" in res.cookies
    assert User.objects.get(email="student@test.com").check_password("Str0ng!Pass")


def test_register_rejects_duplicate_email(client):
    _register(client)
    res = _register(client, email="student@test.com")
    assert res.status_code == 400
    assert "email" in res.json()


def test_register_rejects_password_mismatch(client):
    res = client.post(
        f"{BASE}/register/",
        {
            "email": "a@b.com",
            "password": "Str0ng!Pass",
            "password_confirm": "different",
        },
        format="json",
    )
    assert res.status_code == 400
    assert "password_confirm" in res.json()


def test_login_sets_cookies_and_me_returns_user(client):
    _register(client)
    res = client.post(
        f"{BASE}/login/",
        {"email": "student@test.com", "password": "Str0ng!Pass"},
        format="json",
    )
    assert res.status_code == 200
    assert res.json()["email"] == "student@test.com"
    assert "access_token" in res.cookies

    # The test client persists response cookies automatically — /me should
    # authenticate via the access_token cookie set by login.
    me = client.get(f"{BASE}/me/")
    assert me.status_code == 200
    assert me.json()["email"] == "student@test.com"


def test_me_rejects_anonymous(client):
    res = client.get(f"{BASE}/me/")
    assert res.status_code in (401, 403)


def test_refresh_rotates_cookies(client):
    _register(client)
    login = client.post(
        f"{BASE}/login/",
        {"email": "student@test.com", "password": "Str0ng!Pass"},
        format="json",
    )
    # Test client cookie jar already holds refresh_token from the login response.
    res = client.post(f"{BASE}/refresh/")
    assert res.status_code == 200
    assert "access_token" in res.cookies
    # Rotation: a NEW refresh token is issued.
    assert res.cookies["refresh_token"].value != login.cookies["refresh_token"].value


def test_logout_clears_cookies(client):
    _register(client)
    res = client.post(f"{BASE}/logout/")
    assert res.status_code == 200
    # Deleted cookies come back with empty value / max-age 0.
    for name in ("access_token", "refresh_token"):
        assert res.cookies[name].value == ""
