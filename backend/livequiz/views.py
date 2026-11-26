"""Live quiz REST endpoints — create (senior), lobby info, join."""

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from questions.services import visible_to_students

from .models import LiveQuiz, LiveQuizParticipant


class CreateQuizSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=120, default="Live Quiz")
    question_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1, max_length=30)
    time_limit = serializers.IntegerField(min_value=5, max_value=120, default=20)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create(request):
    """Senior creates a live quiz room from selected questions."""
    if not (request.user.role == "senior" and request.user.senior_approved) and not request.user.is_staff:
        return Response({"detail": "Seniors only."}, status=403)
    s = CreateQuizSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    # Seniors may quiz on any existing question — scheduled/draft included
    # (they authored it; visibility rules apply to students, not the host).
    qs = list(Question.objects.filter(id__in=s.validated_data["question_ids"]))
    if len(qs) != len(s.validated_data["question_ids"]):
        return Response({"detail": "Some question IDs do not exist."}, status=400)
    quiz = LiveQuiz.create(request.user, s.validated_data["title"], qs, s.validated_data["time_limit"])
    return Response({"code": quiz.code, "title": quiz.title}, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def info(request, code):
    """Lobby info for a room code — players poll or use WS 'state'."""
    quiz = get_object_or_404(LiveQuiz, code=code.upper())
    players = LiveQuizParticipant.objects.filter(quiz=quiz).select_related("user")
    return Response(
        {
            "code": quiz.code,
            "title": quiz.title,
            "status": quiz.status,
            "host_name": quiz.host.full_name or quiz.host.email,
            "player_count": players.count(),
            "players": [
                {"name": p.user.full_name or p.user.email, "score": p.score}
                for p in players.order_by("-score")[:10]
            ],
            "is_host": quiz.host_id == request.user.id,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_quizzes(request):
    """Quizzes the user hosts or joined."""
    hosted = LiveQuiz.objects.filter(host=request.user).order_by("-created_at")[:10]
    joined = LiveQuiz.objects.filter(participants__user=request.user).order_by("-created_at")[:10]
    seen, out = set(), []
    for q in list(hosted) + list(joined):
        if q.id not in seen:
            seen.add(q.id)
            out.append({"code": q.code, "title": q.title, "status": q.status})
    return Response(out)
