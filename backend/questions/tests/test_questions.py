"""Question API tests — answer-leak proof, scheduling, validation,
shuffle determinism, and role permissions."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from questions.models import Question, Topic

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def senior(db):
    return User.objects.create_user(
        email="senior@t.dev", password="x", role=User.Role.SENIOR, senior_approved=True
    )


@pytest.fixture
def unapproved_senior(db):
    return User.objects.create_user(
        email="unapp@t.dev", password="x", role=User.Role.SENIOR, senior_approved=False
    )


@pytest.fixture
def student(db):
    return User.objects.create_user(email="stu@t.dev", password="x")


@pytest.fixture
def topic(db):
    return Topic.objects.create(name="Loops", slug="loops", order=1)


def _client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def _payload(topic, **over):
    data = {
        "topic_id": topic.id,
        "type": "mcq_single",
        "title": "Q?",
        "body_markdown": "What is 1+1?",
        "difficulty": "easy",
        "options_input": [
            {"text": "2", "is_correct": True},
            {"text": "3", "is_correct": False},
        ],
    }
    data.update(over)
    return data


def _create(client, topic, **over):
    return client.post("/api/v1/questions/senior/questions/", _payload(topic, **over), format="json")


# ---------- C1: students never see answer data ----------


def test_student_payload_contains_no_answer_data(senior, student, topic):
    res = _create(_client(senior), topic)
    assert res.status_code == 201, res.json()
    qid = res.json()["id"]

    # Force it live.
    Question.objects.filter(pk=qid).update(
        status=Question.Status.PUBLISHED, release_at=timezone.now() - timezone.timedelta(minutes=1)
    )

    res = _client(student).get(f"/api/v1/questions/{qid}/")
    assert res.status_code == 200
    body = res.json()

    # Recursive scan: no key named is_correct or explanation anywhere.
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert k not in ("is_correct", "explanation_markdown", "explanation")
                walk(v)
        elif isinstance(obj, list):
            for i in obj:
                walk(i)

    walk(body)
    assert "options" in body and body["options"]


def test_today_lists_only_visible_questions(senior, student, topic):
    _create(_client(senior), topic)  # draft — invisible
    res = _client(student).get("/api/v1/questions/today/")
    assert res.status_code == 200
    assert res.json() == []


# ---------- C2: scheduling ----------


def test_future_release_is_invisible_to_students(senior, student, topic):
    future = timezone.now() + timezone.timedelta(days=2)
    res = _create(_client(senior), topic, release_at=future.isoformat())
    assert res.status_code == 201
    assert res.json()["status"] == "scheduled"

    res = _client(student).get("/api/v1/questions/today/")
    assert res.json() == []


def test_published_and_released_is_visible(senior, student, topic):
    past = (timezone.now() - timezone.timedelta(minutes=5)).isoformat()
    res = _create(_client(senior), topic, release_at=past)
    qid = res.json()["id"]
    res = _client(student).get(f"/api/v1/questions/{qid}/")
    assert res.status_code == 200


def test_scheduled_question_becomes_visible_after_release(senior, student, topic):
    future = timezone.now() + timezone.timedelta(seconds=1)
    res = _create(_client(senior), topic, release_at=future.isoformat())
    qid = res.json()["id"]
    assert _client(student).get(f"/api/v1/questions/{qid}/").status_code == 404
    import time

    time.sleep(1.2)
    # release_at has passed — query-time visibility makes it live with no
    # background job and no status flip required.
    res = _client(student).get(f"/api/v1/questions/{qid}/")
    assert res.status_code == 200


# ---------- Validation rules ----------


def test_mcq_needs_at_least_2_options(senior, topic):
    res = _create(_client(senior), topic, options_input=[{"text": "only", "is_correct": True}])
    assert res.status_code == 400


def test_mcq_needs_a_correct_option(senior, topic):
    res = _create(
        _client(senior),
        topic,
        options_input=[{"text": "a"}, {"text": "b"}],
    )
    assert res.status_code == 400


def test_single_choice_requires_exactly_one_correct(senior, topic):
    res = _create(
        _client(senior),
        topic,
        options_input=[
            {"text": "a", "is_correct": True},
            {"text": "b", "is_correct": True},
        ],
    )
    assert res.status_code == 400


def test_multi_choice_allows_multiple_correct(senior, topic):
    res = _create(
        _client(senior),
        topic,
        type="mcq_multi",
        options_input=[
            {"text": "a", "is_correct": True},
            {"text": "b", "is_correct": True},
            {"text": "c", "is_correct": False},
        ],
    )
    assert res.status_code == 201, res.json()


# ---------- Shuffle determinism ----------


def test_option_order_is_deterministic_per_user(senior, student, topic):
    res = _create(
        _client(senior),
        topic,
        options_input=[{"text": f"opt{i}", "is_correct": i == 0} for i in range(5)],
    )
    qid = res.json()["id"]
    Question.objects.filter(pk=qid).update(status="published", release_at=timezone.now())

    other = User.objects.create_user(email="stu2@t.dev", password="x")
    orders = {}
    for u in (student, other):
        c = _client(u)
        orders[u.id] = [o["id"] for o in c.get(f"/api/v1/questions/{qid}/").json()["options"]]
        # Same user, second fetch -> identical order.
        assert [o["id"] for o in c.get(f"/api/v1/questions/{qid}/").json()["options"]] == orders[u.id]
    # Different users very likely see different orders (5! permutations).
    assert orders[student.id] != orders[other.id]


# ---------- Permissions ----------


def test_student_cannot_access_senior_endpoints(student, topic):
    c = _client(student)
    assert c.get("/api/v1/questions/senior/questions/").status_code == 403
    assert c.post("/api/v1/questions/senior/questions/", _payload(topic), format="json").status_code == 403


def test_unapproved_senior_is_denied(unapproved_senior, topic):
    c = _client(unapproved_senior)
    assert c.get("/api/v1/questions/senior/questions/").status_code == 403


def test_admin_sees_all_questions(senior, student, topic):
    admin = User.objects.create_user(email="admin@t.dev", password="x", role=User.Role.ADMIN, is_staff=True)
    _create(_client(senior), topic, title="Senior Q")
    _create(_client(admin), topic, title="Admin Q")
    res = _client(admin).get("/api/v1/questions/senior/questions/")
    data = res.json()
    rows = data["results"] if isinstance(data, dict) else data
    titles = {q["title"] for q in rows}
    assert "Admin Q" in titles
    assert "Senior Q" in titles


# ---------- Duplicate ----------


def test_duplicate_creates_draft_copy(senior, topic):
    res = _create(_client(senior), topic, title="Original")
    qid = res.json()["id"]
    res = _client(senior).post(f"/api/v1/questions/senior/questions/{qid}/duplicate/")
    assert res.status_code == 201
    assert res.json()["title"] == "Original (copy)"
    assert res.json()["status"] == "draft"
    assert len(res.json()["options"]) == 2
    assert Question.objects.filter(title="Original (copy)").count() == 1


# ---------- Preview ----------


def test_preview_hides_answers(senior, topic):
    res = _create(_client(senior), topic)
    qid = res.json()["id"]
    res = _client(senior).get(f"/api/v1/questions/senior/questions/{qid}/preview/")
    assert res.status_code == 200
    assert "is_correct" not in str(res.json())
    assert "explanation" not in str(res.json()).lower()
