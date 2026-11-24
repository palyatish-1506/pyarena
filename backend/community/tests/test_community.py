"""M5 tests — badges, levels, comment gating/moderation."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from questions.models import Option, Question, Topic
from submissions.models import Submission

User = get_user_model()
pytestmark = pytest.mark.django_db


def _user(email, **kw):
    return User.objects.create_user(email=email, password="x", **kw)


def _q(author):
    t = Topic.objects.first() or Topic.objects.create(name="T", slug="t", order=0)
    q = Question.objects.create(
        author=author,
        topic=t,
        type="mcq_single",
        title="q",
        body_markdown="b",
        difficulty="easy",
        base_points=10,
        status="published",
        release_at=timezone.now() - timedelta(hours=1),
    )
    o = Option.objects.create(question=q, text="a", is_correct=True, order=0)
    return q, o


def _auth(u):
    c = APIClient()
    c.force_authenticate(u)
    return c


@pytest.fixture(autouse=True)
def _no_throttle(settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": "100000/hour",
        "user": "100000/hour",
        "login": "100000/min",
        "register": "100000/hour",
        "submit": "100000/min",
    }
    settings.COMMENT_BAD_WORDS = ["badword"]


# ---------- badges ----------


def test_first_answer_badge_awarded_once():
    from gamification.services import evaluate_after_submission

    u = _user("b1@t.dev")
    q, o = _q(u)
    s = Submission.objects.create(user=u, question=q, selected_option_ids=[o.id], is_correct=True)
    earned = evaluate_after_submission(u, s)
    assert "first_answer" in earned
    # Idempotent — second evaluation awards nothing new.
    assert evaluate_after_submission(u, s) == []


def test_level_thresholds():
    from submissions.services import level_for

    assert level_for(0) == 1
    assert level_for(99) == 1
    assert level_for(100) == 2
    assert level_for(300) == 3
    assert level_for(700) == 4
    assert level_for(1500) == 5
    assert level_for(3000) == 6
    assert level_for(9999) == 6


def test_hard_correct_badge_only_on_hard():
    from gamification.services import evaluate_after_submission

    u = _user("b2@t.dev")
    t = Topic.objects.first() or Topic.objects.create(name="T2", slug="t2", order=1)
    q = Question.objects.create(
        author=u,
        topic=t,
        type="mcq_single",
        title="h",
        body_markdown="b",
        difficulty="hard",
        base_points=30,
        status="published",
        release_at=timezone.now() - timedelta(hours=1),
    )
    o = Option.objects.create(question=q, text="a", is_correct=True, order=0)
    s = Submission.objects.create(user=u, question=q, selected_option_ids=[o.id], is_correct=True)
    assert "first_hard_correct" in evaluate_after_submission(u, s)


# ---------- comments ----------


def test_comments_403_before_submit():
    student = _user("c1@t.dev")
    senior = _user("sr@t.dev", role="senior", senior_approved=True)
    q, _ = _q(senior)
    res = _auth(student).get(f"/api/v1/questions/{q.id}/comments/")
    assert res.status_code == 403


def test_comment_flow_after_submit():
    senior = _user("sr2@t.dev", role="senior", senior_approved=True)
    student = _user("c2@t.dev")
    other = _user("c3@t.dev")
    q, o = _q(senior)
    # Student submits -> can now comment.
    Submission.objects.create(user=student, question=q, selected_option_ids=[o.id], is_correct=True)
    c = _auth(student)
    res = c.post(f"/api/v1/questions/{q.id}/comments/", {"body": "why option A?"}, format="json")
    assert res.status_code == 201
    cid = res.json()["id"]

    # Another user who hasn't submitted still gets 403.
    assert _auth(other).get(f"/api/v1/questions/{q.id}/comments/").status_code == 403

    # Senior sees thread, accepts the answer.
    sres = _auth(senior).get(f"/api/v1/questions/{q.id}/comments/")
    assert sres.status_code == 200
    assert sres.json()["results"][0]["body"] == "why option A?"
    ares = _auth(senior).post(f"/api/v1/comments/{cid}/accept/")
    assert ares.status_code == 200 and ares.json()["is_accepted"] is True


def test_comment_threading_one_level_and_profanity():
    senior = _user("sr3@t.dev", role="senior", senior_approved=True)
    student = _user("c4@t.dev")
    q, o = _q(senior)
    Submission.objects.create(user=student, question=q, selected_option_ids=[o.id], is_correct=True)
    c = _auth(student)
    r1 = c.post(f"/api/v1/questions/{q.id}/comments/", {"body": "top"}, format="json").json()
    r2 = c.post(f"/api/v1/questions/{q.id}/comments/", {"body": "reply", "parent": r1["id"]}, format="json")
    assert r2.status_code == 201
    # Reply-to-reply rejected (one level only).
    r3 = c.post(
        f"/api/v1/questions/{q.id}/comments/", {"body": "deep", "parent": r2.json()["id"]}, format="json"
    )
    assert r3.status_code == 400
    # Profanity blocked.
    bad = c.post(f"/api/v1/questions/{q.id}/comments/", {"body": "this is badword stuff"}, format="json")
    assert bad.status_code == 400


def test_upvote_and_report():
    senior = _user("sr4@t.dev", role="senior", senior_approved=True)
    student = _user("c5@t.dev")
    q, o = _q(senior)
    Submission.objects.create(user=student, question=q, selected_option_ids=[o.id], is_correct=True)
    c = _auth(student)
    cid = c.post(f"/api/v1/questions/{q.id}/comments/", {"body": "hi"}, format="json").json()["id"]
    assert c.post(f"/api/v1/comments/{cid}/upvote/").json()["upvotes"] == 1
    assert c.post(f"/api/v1/comments/{cid}/report/").json()["report_count"] == 1
