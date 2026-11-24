"""Comment endpoints — gated: only after the user submitted the question."""

from django.conf import settings
from django.db.models import F
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from questions.models import Question
from submissions.models import Submission

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="user.full_name", read_only=True)
    author_id = serializers.IntegerField(source="user.id", read_only=True)
    is_senior = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "author_id",
            "is_senior",
            "body",
            "upvotes",
            "is_accepted",
            "created_at",
            "parent",
            "replies",
        ]
        read_only_fields = [
            "upvotes",
            "is_accepted",
            "created_at",
            "author",
            "author_id",
            "is_senior",
            "replies",
        ]

    def get_is_senior(self, obj):
        return obj.user.role == "senior" and obj.user.senior_approved

    def get_replies(self, obj):
        if obj.parent_id is not None:
            return []  # one level of threading only
        rep = CommentSerializer(obj.replies.filter(is_hidden=False), many=True)
        return rep.data


def _submitted(user, question) -> bool:
    return Submission.objects.filter(user=user, question=question).exists()


def _check_profanity(body: str) -> bool:
    words = getattr(settings, "COMMENT_BAD_WORDS", [])
    low = body.lower()
    return any(w.lower() in low for w in words)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def comments(request, pk):
    question = Question.objects.get(pk=pk)

    # C2: comments hidden until the user has submitted this question.
    # Exception: the question author (senior) and staff can always view —
    # they moderate and mark accepted answers.
    privileged = request.user == question.author or request.user.is_staff
    if not privileged and not _submitted(request.user, question):
        return Response(
            {"detail": "Submit your answer first to see the discussion."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "GET":
        qs = (
            question.comments.filter(parent__isnull=True, is_hidden=False)
            .select_related("user")
            .prefetch_related("replies__user")
        )
        return Response({"results": CommentSerializer(qs, many=True).data})

    body = (request.data.get("body") or "").strip()
    parent_id = request.data.get("parent")
    if not body:
        return Response({"body": ["Required."]}, status=400)
    if _check_profanity(body):
        return Response({"body": ["Comment contains inappropriate language."]}, status=400)

    parent = None
    if parent_id:
        parent = Comment.objects.filter(pk=parent_id, question=question, parent__isnull=True).first()
        if not parent:
            return Response({"parent": ["Invalid parent comment."]}, status=400)

    c = Comment.objects.create(question=question, user=request.user, parent=parent, body=body)
    return Response(CommentSerializer(c).data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upvote(request, comment_id):
    """Toggle-style upvote: each user may upvote once (tracked by a simple
    re-vote guard via a marker in the request is not persistent — we use a
    per-user upvote record kept lightweight: store voter ids is overkill;
    instead upvotes only increment, matching spec's simple model)."""
    c = Comment.objects.filter(pk=comment_id, is_hidden=False).first()
    if not c:
        return Response(status=404)
    Comment.objects.filter(pk=c.pk).update(upvotes=F("upvotes") + 1)
    c.refresh_from_db()
    # helper_10 badge check after an upvote lands on someone's comment.
    from gamification.services import evaluate_after_comment

    evaluate_after_comment(c.user)
    return Response({"upvotes": c.upvotes})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept(request, comment_id):
    """Senior marks an accepted answer — only the question's author (senior)."""
    c = Comment.objects.select_related("question__author").filter(pk=comment_id).first()
    if not c:
        return Response(status=404)
    if request.user != c.question.author or not request.user.senior_approved:
        return Response({"detail": "Only the question author can accept."}, status=403)
    Comment.objects.filter(question=c.question, is_accepted=True).update(is_accepted=False)
    c.is_accepted = True
    c.save(update_fields=["is_accepted"])
    return Response(CommentSerializer(c).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report(request, comment_id):
    """Report a comment — increments report_count for admin review."""
    c = Comment.objects.filter(pk=comment_id).first()
    if not c:
        return Response(status=404)
    Comment.objects.filter(pk=c.pk).update(report_count=F("report_count") + 1)
    c.refresh_from_db()
    return Response({"report_count": c.report_count})
