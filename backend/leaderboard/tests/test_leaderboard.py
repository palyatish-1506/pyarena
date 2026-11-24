"""Leaderboard tests — scopes, ties, week reset, query count."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from gamification.models import Season
from submissions.models import Submission

User = get_user_model()
pytestmark = pytest.mark.django_db


def _user(email, xp=0, level=1, division="A"):
    return User.objects.create_user(email=email, password="x", xp=xp, level=level, division=division)


def _sub(user, points, when=None):
    from questions.models import Option, Question, Topic

    topic = Topic.objects.first() or Topic.objects.create(name="T", slug="t", order=0)
    q = Question.objects.create(
        author=user,
        topic=topic,
        type="mcq_single",
        title="q",
        body_markdown="b",
        difficulty="easy",
        base_points=10,
        status="published",
        release_at=timezone.now() - timedelta(days=1),
    )
    opt = Option.objects.create(question=q, text="a", is_correct=True, order=0)
    sub = Submission.objects.create(
        user=user,
        question=q,
        selected_option_ids=[opt.id],
        is_correct=True,
        points_awarded=points,
    )
    if when:
        Submission.objects.filter(pk=sub.pk).update(submitted_at=when)
    return sub


@pytest.fixture(autouse=True)
def _fresh_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def test_weekly_ranking_and_me_block(client):
    a = _user("a@t.dev")
    b = _user("b@t.dev")
    _sub(a, 50)
    _sub(b, 30)
    res = client.get("/api/v1/leaderboard/?scope=weekly")
    assert res.status_code == 200
    rows = res.json()["rows"]
    assert rows[0]["user_id"] == a.id and rows[0]["score"] == 50
    assert rows[1]["rank"] == 2


def test_ties_share_rank(client):
    a = _user("a@t.dev")
    b = _user("b@t.dev")
    _sub(a, 50)
    _sub(b, 50)
    res = client.get("/api/v1/leaderboard/?scope=weekly")
    ranks = {r["user_id"]: r["rank"] for r in res.json()["rows"]}
    assert ranks[a.id] == ranks[b.id] == 1  # RANK() ties


def test_last_week_submissions_excluded(client):
    from leaderboard.services import week_bounds

    _, last_start = week_bounds()
    old_when = last_start - timedelta(hours=1)  # before this Monday
    u = _user("old@t.dev")
    _sub(u, 999, when=old_when)
    res = client.get("/api/v1/leaderboard/?scope=weekly")
    assert res.json()["rows"] == []


def test_division_scope_filters(client):
    a = _user("a@t.dev", division="A")
    b = _user("b@t.dev", division="B")
    _sub(a, 40)
    _sub(b, 90)
    res = client.get("/api/v1/leaderboard/?scope=division&division=B")
    rows = res.json()["rows"]
    assert len(rows) == 1 and rows[0]["user_id"] == b.id


def test_beginner_scope_excludes_level3plus(client):
    low = _user("low@t.dev", level=2)
    high = _user("high@t.dev", level=5)
    _sub(low, 10)
    _sub(high, 99)
    res = client.get("/api/v1/leaderboard/?scope=beginner")
    rows = res.json()["rows"]
    assert [r["user_id"] for r in rows] == [low.id]


def test_division_battle_averages(client):
    a1 = _user("a1@t.dev", division="A")
    a2 = _user("a2@t.dev", division="A")
    b1 = _user("b1@t.dev", division="B")
    _sub(a1, 30)
    _sub(a2, 30)
    _sub(b1, 90)
    res = client.get("/api/v1/leaderboard/?scope=division_battle")
    rows = res.json()["rows"]
    assert rows[0]["division"] == "B" and rows[0]["avg_per_member"] == 90
    assert rows[1]["division"] == "A" and rows[1]["avg_per_member"] == 30


def test_season_scope_uses_active_season(client):
    u = _user("s@t.dev")
    Season.objects.create(
        name="S1",
        start_date=timezone.now().date() - timedelta(days=1),
        end_date=timezone.now().date() + timedelta(days=30),
        is_active=True,
    )
    _sub(u, 25)
    res = client.get("/api/v1/leaderboard/?scope=season")
    assert res.json()["rows"][0]["score"] == 25


def test_me_block_shows_own_rank_and_gap(client):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    me = _user("me@t.dev")
    other = _user("o@t.dev")
    _sub(other, 50)
    _sub(me, 20)
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(me).access_token}")
    res = c.get("/api/v1/leaderboard/?scope=weekly")
    me_block = res.json()["me"]
    assert me_block["rank"] == 2
    assert me_block["score"] == 20
    assert me_block["gap_to_next"] == 30


def test_query_count_bounded(client):
    for i in range(5):
        u = _user(f"q{i}@t.dev")
        _sub(u, 10 * (i + 1))
    with CaptureQueriesContext(connection) as ctx:
        client.get("/api/v1/leaderboard/?scope=weekly")
    assert len(ctx.captured_queries) <= 6  # scores+rank (1) + users hydrate (1) + session(0 anon)
