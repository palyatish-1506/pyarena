"""Code grading service.

Execution NEVER happens in our own server process — we send the code to
Piston (https://github.com/engineer-man/piston), a sandboxed code-execution
API. Piston runs each submission in an isolated container with time/memory
limits. Free public instance; self-hostable for higher limits.

Why not trust the browser? The client runs visible tests via Pyodide for
instant feedback, but POINTS are only awarded from server-side grading of
ALL tests (including hidden ones the client never sees).
"""

import difflib
import os

import requests

PISTON_URL = os.environ.get("PISTON_URL", "https://emkc.org/api/v2/piston")
PISTON_TIMEOUT = 15

ERROR_EXPLANATIONS = {  # noqa: E501
    "IndentationError": "Check your indentation — Python is strict about spaces. Each block needs consistent leading spaces (usually 4).",  # noqa: E501
    "SyntaxError": "Python couldn't understand that line — check for missing colons (:), brackets, or quotes.",  # noqa: E501
    "NameError": "You're using a variable or function that doesn't exist yet — check for typos or missing definitions.",  # noqa: E501
    "TypeError": "You're doing something a type doesn't support — e.g., adding a string to a number. Check your variable types.",  # noqa: E501
    "IndexError": "You're accessing a list index that doesn't exist — lists start at 0 and end at len-1.",
    "ZeroDivisionError": "You're dividing by zero — check your denominator before dividing.",
    "KeyError": "You're looking up a dictionary key that doesn't exist — check the key spelling.",
    "ValueError": "A function got a value of the right type but wrong content — e.g., int('abc').",
    "AttributeError": "That object doesn't have that attribute — check the variable's type and method names.",
    "RecursionError": "Your function called itself too many times — check your base case.",
    "TimeoutError": "Your code took too long — look for infinite loops or very slow operations.",
    "MemoryError": "Your code used too much memory — check for huge lists or unbounded loops.",
}


def explain_error(stderr: str) -> str:
    """Map a Python traceback's last exception to a beginner-friendly hint."""
    if not stderr:
        return ""
    # Last line of a Python traceback looks like 'ZeroDivisionError: msg'
    last = stderr.strip().splitlines()[-1] if stderr.strip() else ""
    for key in ERROR_EXPLANATIONS:
        if key in last or key in stderr:
            return ERROR_EXPLANATIONS[key]
    return "Check the error message above for details."


def run_on_piston(code: str, stdin: str, time_limit_ms: int, memory_mb: int) -> dict:
    """Execute code on Piston. Returns {stdout, stderr, code, signal}."""
    try:
        r = requests.post(
            f"{PISTON_URL}/execute",
            json={
                "language": "python",
                "version": "3.12",
                "files": [{"name": "main.py", "content": code}],
                "stdin": stdin,
                "run_timeout": max(1000, time_limit_ms),
                "run_memory_limit": memory_mb,
            },
            timeout=PISTON_TIMEOUT,
        )
        r.raise_for_status()
        run = r.json().get("run", {})
        return {
            "stdout": run.get("stdout", ""),
            "stderr": run.get("stderr", ""),
            "code": run.get("code", -1),
            "signal": run.get("signal", None),
        }
    except requests.RequestException as e:
        return {"stdout": "", "stderr": f"Judge unavailable: {e}", "code": -1, "signal": None}


def _norm(s: str) -> str:
    return "\n".join(line.rstrip() for line in s.strip().splitlines())


def similarity_ratio(code_a: str, code_b: str) -> float:
    """0..1 similarity between two submissions (normalized whitespace)."""
    return difflib.SequenceMatcher(None, _norm(code_a), _norm(code_b)).ratio()


def check_similarity(user, problem, code: str, threshold: float = 0.92) -> bool:
    """Flag if this code is near-identical to ANOTHER user's accepted/graded
    submission on the same problem. Flag only — never auto-punish."""
    from .models import CodeSubmission

    others = (
        CodeSubmission.objects.filter(problem=problem)
        .exclude(user=user)
        .exclude(code="")
        .order_by("-created_at")[:50]
    )
    for sub in others:
        if similarity_ratio(code, sub.code) >= threshold:
            return True
    return False
