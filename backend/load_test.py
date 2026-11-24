"""Async load test — 450 virtual students, ~2 min quiz-night scenario.

Replaces Locust on Windows (gevent blocked by App Control). Same shape:
login -> fetch today -> submit answer -> leaderboard.

Run:  python load_test.py [--users 450] [--seconds 120] [--base http://localhost:8000]
Writes docs/load-tests/report-<ts>.md
"""

import argparse
import asyncio
import random
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path

import aiohttp

RESULTS = []  # (endpoint, latency_ms, status)
ERRORS = 0


async def one_user(session, idx, duration, base):
    """Simulate one student's session for `duration` seconds."""
    global ERRORS
    email = f"perf{idx % 450}@t.dev"
    end = time.time() + duration
    t_login = time.perf_counter()
    async with session.post(
        f"{base}/api/v1/auth/login/",
        json={"email": email, "password": "Load!Test234"},
    ) as r:
        RESULTS.append(("login", (time.perf_counter() - t_login) * 1000, r.status))
        if r.status != 200:
            ERRORS += 1
            return
        data = await r.json()
        token = data.get("access", "")
        headers = {"Authorization": f"Bearer {token}"}

    while time.time() < end:
        # today questions
        t0 = time.perf_counter()
        async with session.get(f"{base}/api/v1/questions/today/", headers=headers) as r:
            lat = (time.perf_counter() - t0) * 1000
            RESULTS.append(("today", lat, r.status))
            if r.status != 200:
                ERRORS += 1
                continue
            qs = await r.json()
            if isinstance(qs, dict):
                qs = qs.get("results", [])
            if qs:
                q = random.choice(qs)
                opts = q.get("options", [])
                if opts:
                    opt = random.choice(opts)["id"]
                    t0 = time.perf_counter()
                    async with session.post(
                        f"{base}/api/v1/questions/{q['id']}/submit/",
                        json={"selected_option_ids": [opt], "time_taken_ms": 5000},
                        headers=headers,
                    ) as sr:
                        RESULTS.append(("submit", (time.perf_counter() - t0) * 1000, sr.status))
                        if sr.status not in (200, 201, 409):
                            ERRORS += 1
        # leaderboard
        t0 = time.perf_counter()
        async with session.get(f"{base}/api/v1/leaderboard/?scope=weekly", headers=headers) as r:
            RESULTS.append(("leaderboard", (time.perf_counter() - t0) * 1000, r.status))
            if r.status != 200:
                ERRORS += 1
        await asyncio.sleep(random.uniform(1, 3))


async def main(users, seconds, base):
    connector = aiohttp.TCPConnector(limit=users + 50)
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        await asyncio.gather(*(one_user(session, i, seconds, base) for i in range(users)))


def pct(values, p):
    if not values:
        return 0
    values = sorted(values)
    return values[min(len(values) - 1, int(len(values) * p / 100))]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=450)
    ap.add_argument("--seconds", type=int, default=120)
    ap.add_argument("--base", default="http://localhost:8000")
    args = ap.parse_args()

    t0 = time.time()
    asyncio.run(main(args.users, args.seconds, args.base))
    wall = time.time() - t0

    by_ep = {}
    for ep, lat, status in RESULTS:
        by_ep.setdefault(ep, []).append((lat, status))

    lines = [
        f"# Load test report — {datetime.now(UTC):%Y-%m-%d %H:%M} UTC",
        "",
        f"- Users: {args.users} virtual | Duration: {args.seconds}s scenario ({wall:.0f}s wall)",
        "- Target: p95 < 800ms, errors < 1%",
        f"- Total requests: {len(RESULTS)} | Errors: {ERRORS} ({ERRORS / max(1, len(RESULTS)) * 100:.2f}%)",
        "",
        "| Endpoint | Count | p50 (ms) | p95 (ms) | p99 (ms) | Errors |",
        "|---|---|---|---|---|---|",
    ]
    for ep, rows in sorted(by_ep.items()):
        lats = [lat for lat, _ in rows]
        errs = sum(1 for _, s in rows if s >= 400)
        lines.append(
            f"| {ep} | {len(rows)} | {statistics.median(lats):.0f} | "
            f"{pct(lats, 95):.0f} | {pct(lats, 99):.0f} | {errs} |"
        )
    lines += [
        "",
        "## Notes",
        "- Ran against local `runserver` (single-threaded dev server) — "
        "production Gunicorn has 3 workers; treat absolute numbers as a "
        "pessimistic baseline. Re-run against staging for true numbers.",
        "- Locust couldn't run on Windows (gevent DLL blocked); this script "
        "(`backend/load_test.py`) is the equivalent scenario.",
    ]
    out = Path(__file__).parent.parent / "docs" / "load-tests" / f"report-{datetime.now():%Y%m%d-%H%M}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nReport: {out}")
