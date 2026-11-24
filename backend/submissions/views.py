"""Submission endpoints — thin views; scoring lives in services."""

from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from questions.services import visible_to_students

from .models import Submission
from .services import DuplicateSubmission, submit_answer


class SubmitThrottle(UserRateThrottle):
    scope = "submit"  # 30/min per spec


class _SubmitSerializer(serializers.Serializer):
    selected_option_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    time_taken_ms = serializers.IntegerField(required=False, min_value=0, default=0)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SubmitThrottle])
def submit(request, pk):
    """POST /api/v1/questions/{id}/submit — score one attempt."""
    question = get_object_or_404(visible_to_students(), pk=pk)
    s = _SubmitSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    try:
        result = submit_answer(
            request.user,
            question,
            s.validated_data["selected_option_ids"],
            s.validated_data["time_taken_ms"],
        )
    except DuplicateSubmission:
        return Response({"detail": "Already submitted."}, status=status.HTTP_409_CONFLICT)
    return Response(result, status=status.HTTP_201_CREATED)


class HistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class _SubmissionSerializer(serializers.ModelSerializer):
    question_title = serializers.CharField(source="question.title", read_only=True)
    topic_name = serializers.CharField(source="question.topic.name", read_only=True)
    difficulty = serializers.CharField(source="question.difficulty", read_only=True)
    points = serializers.IntegerField(source="points_awarded", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "question",
            "question_title",
            "topic_name",
            "difficulty",
            "selected_option_ids",
            "is_correct",
            "points",
            "is_late",
            "time_taken_ms",
            "submitted_at",
        ]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history(request):
    """GET /api/v1/me/history — paginated submission history."""
    qs = Submission.objects.filter(user=request.user).select_related("question__topic")
    paginator = HistoryPagination()
    page = paginator.paginate_queryset(qs, request)
    return paginator.get_paginated_response(_SubmissionSerializer(page, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def topic_progress(request):
    """GET /api/v1/me/topics — per-topic accuracy + counts."""
    subs = Submission.objects.filter(user=request.user).select_related("question__topic")
    stats = {}
    for sub in subs:
        name = sub.question.topic.name
        st = stats.setdefault(name, {"attempts": 0, "correct": 0})
        st["attempts"] += 1
        st["correct"] += int(sub.is_correct)
    data = [
        {
            "topic": name,
            "attempts": st["attempts"],
            "correct": st["correct"],
            "accuracy": round(st["correct"] / st["attempts"] * 100),
        }
        for name, st in sorted(stats.items())
    ]
    return Response(data)
