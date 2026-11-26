"""C2: server grading — accepted, wrong answer, timeout, runtime error."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from codepractice.models import CodeProblem, CodeSubmission, TestCase
from codepractice.services import explain_error, similarity_ratio

User = get_user_model()
pytestmark = pytest.mark.django_db


def _problem():
    p = CodeProblem.objects.create(
        title="Add two numbers",
        slug="add-two",
        description_markdown="Add a and b.",
        starter_code="a, b = map(int, input().split())\nprint(a + b)",
        is_published=True,
        created_by=User.objects.create_user(email="s@t.dev", password="x"),
        points=100,
    )
    TestCase.objects.create(problem=p, input_data="1 2\n", expected_output="3", order=0)
    TestCase.objects.create(problem=p, input_data="5 7\n", expected_output="12", is_hidden=True, order=1)
    return p


def _piston(stdout="", stderr="", code=0, signal=None):
    return lambda *a, **k: {"stdout": stdout, "stderr": stderr, "code": code, "signal": signal}


@pytest.fixture
def student():
    u = User.objects.create_user(email="st@t.dev", password="x")
    c = APIClient()
    c.force_authenticate(u)
    return c


GOOD = "a, b = map(int, input().split())\nprint(a + b)"


def test_accepted(student):
    p = _problem()
    outs = iter(
        [
            {"stdout": "3\n", "stderr": "", "code": 0, "signal": None},
            {"stdout": "12\n", "stderr": "", "code": 0, "signal": None},
        ]
    )
    with patch("codepractice.views.run_on_piston", side_effect=lambda *a, **k: next(outs)):
        r = student.post(f"/api/v1/problems/{p.slug}/submit/", {"code": GOOD}, format="json")
    assert r.status_code == 201
    assert r.json()["status"] == "accepted"
    assert r.json()["score"] == 100


def test_wrong_answer(student):
    p = _problem()
    outs = iter([{"stdout": "4\n", "stderr": "", "code": 0, "signal": None}] * 2)
    with patch("codepractice.views.run_on_piston", side_effect=lambda *a, **k: next(outs)):
        r = student.post(f"/api/v1/problems/{p.slug}/submit/", {"code": "print(1)"}, format="json")
    assert r.json()["status"] == "wrong_answer"
    assert r.json()["score"] == 0


def test_runtime_error(student):
    p = _problem()
    outs = iter(
        [{"stdout": "", "stderr": "ZeroDivisionError: division by zero", "code": 1, "signal": None}] * 2
    )
    with patch("codepractice.views.run_on_piston", side_effect=lambda *a, **k: next(outs)):
        r = student.post(f"/api/v1/problems/{p.slug}/submit/", {"code": "print(1/0)"}, format="json")
    assert r.json()["status"] == "runtime_error"
    assert "dividing by zero" in r.json()["error_hint"].lower() or r.json()["error_hint"]


def test_timeout_flag(student):
    p = _problem()
    outs = iter([{"stdout": "", "stderr": "", "code": -1, "signal": "SIGKILL"}] * 2)
    with patch("codepractice.views.run_on_piston", side_effect=lambda *a, **k: next(outs)):
        r = student.post(f"/api/v1/problems/{p.slug}/submit/", {"code": "while True: pass"}, format="json")
    assert r.json()["status"] == "timeout"


def test_hidden_tests_not_exposed(student):
    p = _problem()
    r = student.get(f"/api/v1/problems/{p.slug}/")
    assert r.status_code == 200
    data = r.json()
    assert data["hidden_test_count"] == 1
    # hidden expected outputs never appear
    assert all("expected_output" in t for t in data["visible_tests"])
    assert len(data["visible_tests"]) == 1


def test_error_explainer():
    assert "indentation" in explain_error("  File x\nIndentationError: unexpected indent").lower()
    assert "dividing by zero" in explain_error("ZeroDivisionError: div by zero").lower()
    assert explain_error("") == ""


def test_similarity_flags_copy():
    p = _problem()
    u1 = User.objects.create_user(email="a@t.dev", password="x")
    CodeSubmission.objects.create(user=u1, problem=p, code=GOOD)
    assert similarity_ratio(GOOD, GOOD) == 1.0
    assert similarity_ratio(GOOD, "print('hello world this is different')") < 0.5
