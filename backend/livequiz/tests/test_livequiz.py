"""C1: 3 simulated WS clients through a full quiz lifecycle."""

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from config.asgi import application
from livequiz.models import LiveQuiz, LiveQuizParticipant
from questions.models import Option, Question, Topic

User = get_user_model()
pytestmark = pytest.mark.django_db(transaction=True)


def _user(email, **kw):
    return User.objects.create_user(email=email, password="x", **kw)


def _question(author):
    t = Topic.objects.first() or Topic.objects.create(name="T", slug="t", order=0)
    q = Question.objects.create(
        author=author,
        topic=t,
        type="mcq_single",
        title="Q?",
        body_markdown="b",
        difficulty="easy",
        base_points=10,
        status="published",
        release_at=timezone.now() - __import__("datetime").timedelta(hours=1),
    )
    o1 = Option.objects.create(question=q, text="right", is_correct=True, order=0)
    o2 = Option.objects.create(question=q, text="wrong", is_correct=False, order=1)
    return q, o1, o2


def _ws(user, code):
    token = str(AccessToken.for_user(user))
    return WebsocketCommunicator(application, f"/ws/quiz/{code}/?token={token}")


async def _recv_until(comm, event_name, timeout=5):
    """Read messages until the named event arrives; return it."""
    import asyncio

    for _ in range(20):
        msg = await asyncio.wait_for(comm.receive_json_from(), timeout)
        if msg.get("event") == event_name:
            return msg
    raise AssertionError(f"never saw {event_name}")


class LiveQuizFlowTest(TransactionTestCase):
    async def test_full_quiz_three_clients(self):
        host = await database_sync_to_async(_user)("host@t.dev", role="senior", senior_approved=True)
        p1 = await database_sync_to_async(_user)("p1@t.dev")
        p2 = await database_sync_to_async(_user)("p2@t.dev")

        def _mk():
            q1, c1, _ = _question(host)
            q2, _, _ = _question(host)
            quiz = LiveQuiz.create(host, "Quiz!", [q1, q2], time_limit=3)
            return q1, c1, quiz

        q1, correct1, quiz = await database_sync_to_async(_mk)()

        # Connect host + 2 players.
        hc = _ws(host, quiz.code)
        c1 = _ws(p1, quiz.code)
        c2 = _ws(p2, quiz.code)
        await hc.connect()
        await c1.connect()
        await c2.connect()
        try:
            # Everyone gets 'state'.
            for c in (hc, c1, c2):
                st = await asyncio_wait_state(c)
                assert st["quiz"]["code"] == quiz.code
            # Drain any extra state msgs on host/player channels.
            await hc.send_json_to({"action": "start"})
            # Host sees question event.
            qmsg = await _recv_until(hc, "question")
            assert qmsg["index"] == 0 and qmsg["total"] == 2
            # Players answer: p1 correct, p2 wrong.
            await c1.send_json_to({"action": "answer", "option_ids": [correct1.id], "time_taken_ms": 2000})
            await c2.send_json_to({"action": "answer", "option_ids": [999999], "time_taken_ms": 5000})
            # Host reveals manually (deterministic in tests; auto-timer
            # covers production timing).
            await hc.send_json_to({"action": "reveal"})
            rev = await _recv_until(hc, "reveal", timeout=8)
            assert rev["correct_option_ids"] == [correct1.id]
            # Leaderboard shows p1 ahead.
            lb = rev["leaderboard"]
            assert lb and lb[0]["score"] > 0
            # Player also receives reveal.
            prev = await _recv_until(c1, "reveal", timeout=8)
            assert prev["event"] == "reveal"
            # Host advances -> question 2.
            await hc.send_json_to({"action": "next"})
            q2msg = await _recv_until(hc, "question", timeout=8)
            assert q2msg["index"] == 1
            # End quiz.
            await hc.send_json_to({"action": "end"})
            fin = await _recv_until(hc, "finished", timeout=8)
            assert isinstance(fin.get("leaderboard"), list)
            # DB state: participants + scored answers exist.
            counts = await database_sync_to_async(
                lambda: (
                    LiveQuizParticipant.objects.filter(quiz=quiz).count(),
                    __import__("livequiz.models", fromlist=["LiveQuizAnswer"])
                    .LiveQuizAnswer.objects.filter(quiz=quiz, is_correct=True)
                    .exists(),
                )
            )()
            assert counts[0] == 2 and counts[1]
        finally:
            for c in (hc, c1, c2):
                await c.disconnect()


async def asyncio_wait_state(comm):
    import asyncio

    return await asyncio.wait_for(comm.receive_json_from(), 5)
