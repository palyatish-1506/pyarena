"""Question endpoints — thin views; rules live in services/serializers."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Question
from .permissions import IsSeniorOrAdmin
from .serializers import (
    SeniorQuestionSerializer,
    StudentQuestionSerializer,
    TopicSerializer,
)
from .services import duplicate_question, shuffled_options, visible_to_students

# ---------- Student-facing ----------


class TodayQuestionsView(generics.ListAPIView):
    """GET /api/v1/questions/today — published & released questions."""

    serializer_class = StudentQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return visible_to_students()


class QuestionDetailView(generics.RetrieveAPIView):
    """GET /api/v1/questions/{id} — student view, answers hidden."""

    serializer_class = StudentQuestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return visible_to_students()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def topics(request):
    from .models import Topic

    return Response(TopicSerializer(Topic.objects.all(), many=True).data)


# ---------- Senior-facing ----------


class SeniorQuestionListCreate(generics.ListCreateAPIView):
    """GET/POST /api/v1/senior/questions — own questions + create."""

    serializer_class = SeniorQuestionSerializer
    permission_classes = [IsSeniorOrAdmin]

    def get_queryset(self):
        qs = Question.objects.select_related("topic", "author").prefetch_related("options")
        # Seniors see their own; admins see all.
        if self.request.user.role != "admin":
            qs = qs.filter(author=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class SeniorQuestionDetail(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/senior/questions/{id} — owner or admin."""

    serializer_class = SeniorQuestionSerializer
    permission_classes = [IsSeniorOrAdmin]

    def get_queryset(self):
        qs = Question.objects.select_related("topic", "author").prefetch_related("options")
        if self.request.user.role != "admin":
            qs = qs.filter(author=self.request.user)
        return qs


@api_view(["POST"])
@permission_classes([IsSeniorOrAdmin])
def duplicate(request, pk):
    """POST /api/v1/senior/questions/{id}/duplicate — copy as new draft."""
    question = generics.get_object_or_404(Question, pk=pk)
    copy = duplicate_question(question, author=request.user)
    return Response(SeniorQuestionSerializer(copy).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsSeniorOrAdmin])
def preview(request, pk):
    """GET /api/v1/senior/questions/{id}/preview — see it exactly as a
    student would (shuffled options, no answers)."""
    question = generics.get_object_or_404(Question.objects.prefetch_related("options"), pk=pk)
    shuffled = shuffled_options(question, request.user.id)
    # Reuse the student serializer but inject the shuffled options.
    data = StudentQuestionSerializer(question, context={"request": request}).data
    data["options"] = [{"id": o.id, "text": o.text, "order": i} for i, o in enumerate(shuffled)]
    return Response(data)
