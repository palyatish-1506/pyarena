"""Code practice REST endpoints."""

from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CodeProblem, CodeSubmission
from .services import check_similarity, explain_error, run_on_piston


def _problem_payload(p, include_hidden=False):
    tests = p.test_cases.all()
    visible = [t for t in tests if not t.is_hidden]
    hidden = [t for t in tests if t.is_hidden]
    return {
        "id": p.id,
        "slug": p.slug,
        "title": p.title,
        "description_markdown": p.description_markdown,
        "starter_code": p.starter_code,
        "difficulty": p.difficulty,
        "points": p.points,
        "time_limit_ms": p.time_limit_ms,
        "memory_limit_mb": p.memory_limit_mb,
        # Visible tests are sent to the client for practice-mode runs.
        # Hidden tests NEVER leave the server.
        "visible_tests": [{"id": t.id, "input": t.input_data} for t in visible],
        "hidden_test_count": len(hidden),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def problems(request):
    qs = CodeProblem.objects.filter(is_published=True)
    return Response([_problem_payload(p) for p in qs])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def problem_detail(request, slug):
    p = get_object_or_404(CodeProblem, slug=slug, is_published=True)
    # Include expected outputs for visible tests so client can self-check.
    payload = _problem_payload(p)
    visible = {t.id: t for t in p.test_cases.all() if not t.is_hidden}
    for t in payload["visible_tests"]:
        t["expected_output"] = visible[t["id"]].expected_output
    return Response(payload)


class SubmitSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=1, max_length=100_000)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit(request, slug):
    """Grade a submission server-side via Piston — client result NOT trusted."""
    p = get_object_or_404(CodeProblem, slug=slug, is_published=True)
    s = SubmitSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    code = s.validated_data["code"]

    sub = CodeSubmission.objects.create(user=request.user, problem=p, code=code)

    # Run ALL tests (visible + hidden) on the judge.
    results = []
    all_passed = True
    any_timeout = False
    any_runtime = False
    for t in p.test_cases.all():
        out = run_on_piston(code, t.input_data, p.time_limit_ms, p.memory_limit_mb)
        actual = out["stdout"].strip()
        expected = t.expected_output.strip()
        passed = out["code"] == 0 and actual == expected
        results.append(
            {
                "input": t.input_data,
                "expected": expected,
                "actual": actual,
                "stderr": out["stderr"],
                "passed": passed,
                "hidden": t.is_hidden,
            }
        )
        if not passed:
            all_passed = False
            if "Timeout" in out["stderr"] or out["signal"] == "SIGKILL":
                any_timeout = True
            elif out["code"] != 0:
                any_runtime = True

    if all_passed:
        sub.status = CodeSubmission.Status.ACCEPTED
        sub.score = p.points
    elif any_timeout:
        sub.status = CodeSubmission.Status.TIMEOUT
    elif any_runtime and not any(t["passed"] for t in results):
        sub.status = CodeSubmission.Status.RUNTIME_ERROR
    else:
        sub.status = CodeSubmission.Status.WRONG_ANSWER

    sub.results = results
    sub.is_flagged_similar = check_similarity(request.user, p, code)
    sub.save()

    return Response(
        {
            "status": sub.status,
            "score": sub.score,
            "points_possible": p.points,
            "results": results,
            "error_hint": explain_error(next((r["stderr"] for r in results if r["stderr"]), "")),
            "flagged_similar": sub.is_flagged_similar,
            "message": "Flagged for senior review — submissions that are too similar may be reviewed."
            if sub.is_flagged_similar
            else "",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_submissions(request, slug):
    p = get_object_or_404(CodeProblem, slug=slug, is_published=True)
    subs = CodeSubmission.objects.filter(user=request.user, problem=p)[:20]
    return Response(
        [{"id": s.id, "status": s.status, "score": s.score, "created_at": s.created_at} for s in subs]
    )
