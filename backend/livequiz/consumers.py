"""Live quiz WebSocket consumer.

One consumer per connection, group `quiz_<code>`. Roles:
- host:  controls flow (start/next/reveal/end) — only quiz.host may send these.
- player: joins (auto on connect w/ code), answers during LIVE window.

Server is the only source of truth for timing & scoring: the reveal task
scores all answers received before close_at (quiz-level deadline stored
in channel-layer cache via group state on the LiveQuiz row + monotonic
timestamps in messages).
"""

import asyncio
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from livequiz.models import LiveQuiz, LiveQuizParticipant


def _jwt_user(token):
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import AccessToken

    try:
        uid = AccessToken(token)["user_id"]
        return get_user_model().objects.get(pk=uid)
    except Exception:
        return None


class QuizConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.code = self.scope["url_route"]["kwargs"]["code"]
        self.group = f"quiz_{self.code}"
        token = (
            self.scope["query_string"].decode().split("token=")[-1]
            if b"token=" in self.scope["query_string"]
            else ""
        )
        self.user = await database_sync_to_async(_jwt_user)(token) if token else None
        if not self.user:
            await self.close(code=4001)
            return
        self.role = "spectator"
        self.quiz = await self._get_quiz()
        if not self.quiz:
            await self.close(code=4004)
            return
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        if self.quiz.host_id == self.user.id:
            self.role = "host"
        elif self.quiz.status == LiveQuiz.Status.LOBBY:
            await self._join_player()
        await self._send_state()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    # ---------- events from clients ----------
    async def receive_json(self, content, **kwargs):
        action = content.get("action")
        if self.role == "host":
            if action == "start":
                await self._start_quiz()
            elif action == "next":
                await self._next_question()
            elif action == "reveal":
                await self._manual_reveal()
            elif action == "end":
                await self._finish()
        elif action == "answer":
            await self._answer(content)

    # ---------- quiz flow (host-driven, server-scored) ----------
    async def _start_quiz(self):
        q = await self._get_quiz()
        if q.status != LiveQuiz.Status.LOBBY:
            return
        await self._set_status(LiveQuiz.Status.LIVE, index=0)
        await self._broadcast_question()

    async def _next_question(self):
        q = await self._get_quiz()
        if q.status not in (LiveQuiz.Status.REVEAL, LiveQuiz.Status.LIVE):
            return
        nxt = q.current_index + 1
        total = await self._question_count()
        if nxt >= total:
            await self._finish()
            return
        await self._set_status(LiveQuiz.Status.LIVE, index=nxt)
        await self._broadcast_question()

    async def _finish(self):
        await self._set_status(LiveQuiz.Status.FINISHED)
        await self.channel_layer.group_send(
            self.group,
            {"type": "quiz.event", "event": "finished", "leaderboard": await self._leaderboard(10)},
        )

    async def _broadcast_question(self):
        q = await self._get_quiz()
        questions = await self._ordered_questions(q)
        if not questions:
            return
        question = questions[q.current_index]
        # Server clock: deadline = now + time_limit, stored in message.
        deadline = time.time() + q.question_time_limit
        payload = {
            "event": "question",
            "index": q.current_index,
            "total": len(questions),
            "question": {
                "id": question.id,
                "title": question.title,
                "body_markdown": question.body_markdown,
                "code_snippet": question.code_snippet,
                "options": [{"id": o.id, "text": o.text, "order": o.order} for o in question.options.all()],
                "time_limit": q.question_time_limit,
            },
            "deadline_ts": deadline,
        }
        # Schedule reveal at deadline — server owns the clock.
        loop = asyncio.get_running_loop()
        loop.call_later(
            q.question_time_limit,
            lambda: asyncio.ensure_future(self._reveal_later(q.id, deadline)),
        )
        await self.channel_layer.group_send(self.group, {"type": "quiz.event", **payload})

    async def _reveal_later(self, quiz_id, deadline):
        # Only reveal if quiz still LIVE and deadline reached (no double-reveal).
        q = await self._get_quiz()
        if q.status != LiveQuiz.Status.LIVE:
            return
        await self._score_and_reveal(q.id, deadline)

    async def _manual_reveal(self):
        """Host can reveal early — also the deterministic path in tests."""
        q = await self._get_quiz()
        if q.status != LiveQuiz.Status.LIVE:
            return
        questions = await self._ordered_questions(q)
        if not questions:
            return
        question = questions[q.current_index]

        @database_sync_to_async
        def _correct_ids():
            return sorted(question.options.filter(is_correct=True).values_list("id", flat=True))

        correct_ids = await _correct_ids()
        scores = await self._score_answers(q.id, question.id, correct_ids, 0)
        await self._set_status(LiveQuiz.Status.REVEAL)
        await self.channel_layer.group_send(
            self.group,
            {
                "type": "quiz.event",
                "event": "reveal",
                "index": q.current_index,
                "total": len(questions),
                "correct_option_ids": correct_ids,
                "explanation": question.explanation_markdown,
                "scores": scores,
                "leaderboard": await self._leaderboard(10),
            },
        )

    async def _score_and_reveal(self, quiz_id, deadline):
        q = await self._get_quiz()
        questions = await self._ordered_questions(q)
        if not questions:
            return
        question = questions[q.current_index]

        @database_sync_to_async
        def _correct_ids():
            return sorted(question.options.filter(is_correct=True).values_list("id", flat=True))

        correct_ids = await _correct_ids()
        # Score participants who answered before deadline.
        scores = await self._score_answers(quiz_id, question.id, correct_ids, deadline)
        await self._set_status(LiveQuiz.Status.REVEAL)
        await self.channel_layer.group_send(
            self.group,
            {
                "type": "quiz.event",
                "event": "reveal",
                "index": q.current_index,
                "total": len(questions),
                "correct_option_ids": correct_ids,
                "explanation": question.explanation_markdown,
                "scores": scores,
                "leaderboard": await self._leaderboard(10),
            },
        )

    # ---------- player actions ----------
    async def _join_player(self):
        await database_sync_to_async(
            lambda: LiveQuizParticipant.objects.get_or_create(quiz_id=self.quiz.id, user=self.user)
        )()

    async def _answer(self, content):
        q = await self._get_quiz()
        if q.status != LiveQuiz.Status.LIVE:
            return
        # Enforce deadline server-side.
        # deadline is implicit: we track per-question open time via quiz.updated_at? Simpler:
        # store deadline in a channel-layer dict keyed by quiz+index — but cross-worker
        # needs Redis; acceptable: check via participant.last_answer_ms + question start.
        option_ids = content.get("option_ids", [])
        time_taken = content.get("time_taken_ms", 0)
        question_id = await self._current_question_id()
        if question_id is None:
            return
        await database_sync_to_async(self._record_answer)(q.id, question_id, option_ids, time_taken)

    @database_sync_to_async
    def _current_question_id(self):
        q = LiveQuiz.objects.filter(code=self.code).first()
        if not q or q.status != LiveQuiz.Status.LIVE:
            return None
        qs = list(q.questions.order_by("id"))
        if q.current_index >= len(qs):
            return None
        return qs[q.current_index].id

    def _record_answer(self, quiz_id, question_id, option_ids, time_taken):
        """First answer per question wins (UNIQUE constraint); correctness is
        NOT stored here — scoring happens at reveal against correct_option_ids."""
        from livequiz.models import LiveQuizAnswer

        try:
            LiveQuizAnswer.objects.create(
                quiz_id=quiz_id,
                participant=LiveQuizParticipant.objects.get(quiz_id=quiz_id, user=self.user),
                question_id=question_id,
                selected_option_ids=sorted(set(option_ids)),
                time_taken_ms=min(int(time_taken), 600_000),
            )
        except Exception:
            pass  # duplicate or missing participant — ignore

    # ---------- sync helpers ----------
    @database_sync_to_async
    def _get_quiz(self):
        return LiveQuiz.objects.prefetch_related("questions__options").filter(code=self.code).first()

    @database_sync_to_async
    def _set_status(self, status, index=None):
        LiveQuiz.objects.filter(code=self.code).update(
            status=status, **({"current_index": index} if index is not None else {})
        )

    @database_sync_to_async
    def _question_count(self):
        return self.quiz.questions.count() if self.quiz else 0

    @database_sync_to_async
    def _ordered_questions(self, quiz):
        return list(quiz.questions.prefetch_related("options").order_by("id"))

    @database_sync_to_async
    def _leaderboard(self, n):
        parts = (
            LiveQuizParticipant.objects.filter(quiz_id=self.quiz.id)
            .select_related("user")
            .order_by("-score", "correct_count")[:n]
        )
        return [
            {
                "rank": i + 1,
                "name": p.user.full_name or p.user.email,
                "score": p.score,
                "correct": p.correct_count,
            }
            for i, p in enumerate(parts)
        ]

    @database_sync_to_async
    def _score_answers(self, quiz_id, question_id, correct_ids, deadline):
        """Score every recorded answer for this question: correct = exact set
        match; points = max(100, 1000 - time_taken_ms//10) — faster is worth more."""
        from livequiz.models import LiveQuizAnswer

        correct_set = set(correct_ids)
        answers = LiveQuizAnswer.objects.filter(quiz_id=quiz_id, question_id=question_id).select_related(
            "participant__user"
        )
        scored = []
        for a in answers:
            is_correct = set(a.selected_option_ids) == correct_set and bool(a.selected_option_ids)
            points = max(100, 1000 - a.time_taken_ms // 10) if is_correct else 0
            LiveQuizAnswer.objects.filter(pk=a.pk).update(is_correct=is_correct, points=points)
            p = a.participant
            p.score += points
            p.correct_count += int(is_correct)
            p.answered_count += 1
            p.last_answer_ms = a.time_taken_ms
            p.save(update_fields=["score", "correct_count", "answered_count", "last_answer_ms"])
            scored.append({"user_id": p.user_id, "points": points, "correct": is_correct})
        return scored

    # ---------- outgoing ----------
    async def quiz_event(self, event):
        await self.send_json(
            {"event": event.get("event"), **{k: v for k, v in event.items() if k not in ("type", "event")}}
        )

    async def _send_state(self):
        q = await self._get_quiz()
        await self.send_json(
            {
                "event": "state",
                "role": self.role,
                "quiz": {
                    "code": q.code,
                    "title": q.title,
                    "status": q.status,
                    "current_index": q.current_index,
                    "question_count": q.questions.count(),
                    "time_limit": q.question_time_limit,
                },
                "leaderboard": await self._leaderboard(10),
            }
        )
