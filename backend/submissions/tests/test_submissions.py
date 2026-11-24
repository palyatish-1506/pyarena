"""Submission tests — C1 scoring edges, C2 concurrency, streaks, history."""

import threading

import pytest
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from questions.models import Option, Question, Topic
from submissions.models import Submission

User = get_user_model()
pytestmark = pytest.mark.django_db


def make_question(
    topic, *, difficulty="easy", release_hours_ago=1, close_hours_ahead=23, options=None, qtype="mcq_single"
):
    now = timezone.now()
    q = Question.objects.create(
        author=User.objects.create_user(email=f"a{Question.objects.count()}@t.dev", password="x"),
        topic=topic,
        type=qtype,
        title="Q",
        body_markdown="b",
        code_snippet="",
        difficulty=difficulty,
        explanation_markdown="because",
        base_points=Question.BASE_POINTS[difficulty],
        release_at=now - timezone.timedelta(hours=release_hours_ago),
        close_at=now + timezone.timedelta(hours=close_hours_ahead),
        status=Question.Status.PUBLISHED,
    )
    opts = options or [("right", True), ("wrong", False)]
    for i, (text, correct) in enumerate(opts):
        Option.objects.create(question=q, text=text, is_correct=correct, order=i)
    return q


@pytest.fixture
def student(db):
    return User.objects.create_user(email="s@t.dev", password="x")


@pytest.fixture
def topic(db):
    return Topic.objects.create(name="Loops", slug="loops", order=1)


def _client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def _submit(client, qid, ids, ms=1000):
    return client.post(
        f"/api/v1/questions/{qid}/submit/", {"selected_option_ids": ids, "time_taken_ms": ms}, format="json"
    )


@pytest.fixture(autouse=True)
def _no_throttle(settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": "100000/hour",
        "user": "100000/hour",
        "login": "100000/min",
        "register": "100000/hour",
        "submit": "100000/min",
    }


# ---------- C1: scoring ----------


def test_correct_answer_scores_base(student, topic):
    # Mid-window (release 20h ago, close in 4h) -> no speed bonus.
    q = make_question(topic, release_hours_ago=20, close_hours_ahead=4)
    correct = q.options.get(is_correct=True).id
    res = _submit(_client(student), q.id, [correct])
    assert res.status_code == 201
    d = res.json()
    assert d["is_correct"] is True
    assert d["points_awarded"] == 10  # easy base
    assert d["new_xp"] == 10
    assert d["explanation"] == "because"
    assert d["streak"] == 1


def test_wrong_answer_zero_points(student, topic):
    q = make_question(topic)
    wrong = q.options.get(is_correct=False).id
    res = _submit(_client(student), q.id, [wrong])
    assert res.status_code == 201
    assert res.json()["points_awarded"] == 0
    assert res.json()["is_correct"] is False


def test_speed_bonus_first_10_percent(student, topic):
    # release 1h ago, close 23h ahead -> window 24h; now is ~4% in -> +50%.
    q = make_question(topic, release_hours_ago=1, close_hours_ahead=23)
    correct = q.options.get(is_correct=True).id
    res = _submit(_client(student), q.id, [correct])
    assert res.json()["points_awarded"] == 15  # 10 + 5 (50% of base)


def test_no_bonus_after_half_window(student, topic):
    # release 20h ago, close in 4h -> now is ~83% of 24h window -> 0 bonus.
    q = make_question(topic, release_hours_ago=20, close_hours_ahead=4)
    correct = q.options.get(is_correct=True).id
    res = _submit(_client(student), q.id, [correct])
    assert res.json()["points_awarded"] == 10


def test_late_answer_is_practice_zero_points(student, topic):
    q = make_question(topic, release_hours_ago=30, close_hours_ahead=-1)  # closed
    correct = q.options.get(is_correct=True).id
    res = _submit(_client(student), q.id, [correct])
    d = res.json()
    assert d["is_late"] is True
    assert d["points_awarded"] == 0
    assert d["streak"] == 1  # still counts for streak


def test_multi_partial_selection_is_wrong(student, topic):
    q = make_question(
        topic,
        qtype="mcq_multi",
        release_hours_ago=20,
        close_hours_ahead=4,
        options=[("a", True), ("b", True), ("c", False)],
    )
    a = q.options.get(text="a").id
    b = q.options.get(text="b").id
    c = q.options.get(text="c").id
    # Partial: only one of two correct -> wrong.
    res = _submit(_client(student), q.id, [a])
    assert res.json()["is_correct"] is False
    # Full correct set -> correct.
    student2 = User.objects.create_user(email="s2@t.dev", password="x")
    res2 = _submit(_client(student2), q.id, [a, b])
    assert res2.json()["is_correct"] is True
    assert res2.json()["points_awarded"] == 10
    # Including a wrong option -> wrong.
    student3 = User.objects.create_user(email="s3@t.dev", password="x")
    res3 = _submit(_client(student3), q.id, [a, b, c])
    assert res3.json()["is_correct"] is False


def test_duplicate_submit_returns_409(student, topic):
    q = make_question(topic)
    correct = q.options.get(is_correct=True).id
    c = _client(student)
    assert _submit(c, q.id, [correct]).status_code == 201
    res = _submit(c, q.id, [correct])
    assert res.status_code == 409
    assert Submission.objects.filter(user=student, question=q).count() == 1


def test_submit_requires_auth(topic):
    q = make_question(topic)
    res = APIClient().post(f"/api/v1/questions/{q.id}/submit/", {"selected_option_ids": [1]}, format="json")
    assert res.status_code in (401, 403)


# ---------- streaks ----------


def test_streak_increments_across_days(student, topic):
    from datetime import timedelta

    from submissions.services import _ist_today

    today = _ist_today()
    # Pretend last activity was yesterday IST.
    student.last_active_date = today - timedelta(days=1)
    student.current_streak = 4
    student.save()

    q1 = make_question(topic)
    correct = q1.options.get(is_correct=True).id
    res = _submit(_client(student), q1.id, [correct])
    assert res.json()["streak"] == 5


def test_streak_resets_after_missed_days_without_freeze(student, topic):
    from datetime import timedelta

    from submissions.services import _ist_today

    today = _ist_today()
    student.last_active_date = today - timedelta(days=5)
    student.current_streak = 4
    student.streak_freezes = 0
    student.save()

    q = make_question(topic)
    correct = q.options.get(is_correct=True).id
    res = _submit(_client(student), q.id, [correct])
    assert res.json()["streak"] == 1  # reset


def test_freeze_covers_one_missed_day(student, topic):
    from datetime import timedelta

    from submissions.services import _ist_today

    today = _ist_today()
    student.last_active_date = today - timedelta(days=2)  # 1 missed day
    student.current_streak = 4
    student.streak_freezes = 1
    student.save()

    q = make_question(topic)
    correct = q.options.get(is_correct=True).id
    res = _submit(_client(student), q.id, [correct])
    d = res.json()
    assert d["streak"] == 5  # freeze saved the streak
    student.refresh_from_db()
    assert student.streak_freezes == 0


# ---------- history / topics ----------


def test_history_and_topic_progress(student, topic):
    q = make_question(topic)
    correct = q.options.get(is_correct=True).id
    _submit(_client(student), q.id, [correct])

    c = _client(student)
    hist = c.get("/api/v1/me/history/")
    assert hist.status_code == 200
    rows = hist.json()["results"] if "results" in hist.json() else hist.json()
    assert len(rows) == 1
    assert rows[0]["is_correct"] is True

    prog = c.get("/api/v1/me/topics/")
    assert prog.status_code == 200
    assert prog.json()[0]["topic"] == "Loops"
    assert prog.json()[0]["accuracy"] == 100


# ---------- C2: concurrency ----------


class ConcurrentSubmitTest(TransactionTestCase):
    """Two parallel submits for the same (user, question) -> exactly one wins."""

    def test_parallel_submits_exactly_one_succeeds(self):
        topic = Topic.objects.create(name="T", slug="t", order=1)
        user = User.objects.create_user(email="cc@t.dev", password="x")
        q = make_question(topic)
        opt = q.options.get(is_correct=True).id

        results = []

        def attempt():
            c = APIClient()
            c.force_authenticate(user)
            r = c.post(f"/api/v1/questions/{q.id}/submit/", {"selected_option_ids": [opt]}, format="json")
            results.append(r.status_code)

        t1 = threading.Thread(target=attempt)
        t2 = threading.Thread(target=attempt)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert sorted(results).count(201) == 1
        assert 409 in results
        assert Submission.objects.filter(user=user, question=q).count() == 1
