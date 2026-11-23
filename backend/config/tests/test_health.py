"""Smoke test for the walking-skeleton health endpoint."""

import pytest
from django.db import connection


@pytest.mark.django_db
def test_health_endpoint_returns_ok(client):
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"


@pytest.mark.django_db
def test_database_is_reachable():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)
