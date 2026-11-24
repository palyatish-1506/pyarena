"""Locust load test — simulates 450 students during a quiz night.

Run:  locust -f locustfile.py --host http://localhost:8000
      (then open http://localhost:8089, set users=450, spawn rate=50)

Scenario per user: login -> fetch today questions -> answer one ->
check leaderboard. Targets: p95 < 800ms, errors < 1%.
"""

import random

from locust import HttpUser, between, task


class Student(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Unique user per VU iteration cycle — register is throttled, so we
        # login with a shared pool of pre-seeded test accounts instead.
        self.email = f"load{random.randint(1, 450)}@t.dev"
        self.client.post(
            "/api/v1/auth/login/",
            json={"email": self.email, "password": "Load!Test234"},
            name="login",
        )

    @task(3)
    def answer_question(self):
        res = self.client.get("/api/v1/questions/today/", name="today")
        if res.status_code != 200:
            return
        questions = res.json()
        if isinstance(questions, dict):
            questions = questions.get("results", [])
        if not questions:
            return
        q = random.choice(questions)
        # Pick a random option id (correctness doesn't matter for load).
        opts = q.get("options", [])
        if not opts:
            return
        opt_id = random.choice(opts)["id"]
        self.client.post(
            f"/api/v1/questions/{q['id']}/submit/",
            json={"selected_option_ids": [opt_id], "time_taken_ms": 5000},
            name="submit",
        )

    @task(1)
    def leaderboard(self):
        self.client.get("/api/v1/leaderboard/?scope=weekly", name="leaderboard")

    @task(1)
    def profile(self):
        self.client.get("/api/v1/me/", name="me")
