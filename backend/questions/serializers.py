"""Serializers for questions.

Two shapes, on purpose:
- SeniorQuestionSerializer — full read/write incl. options + correctness.
- StudentQuestionSerializer — the ONLY shape students ever receive.
  It has no is_correct / explanation fields at all, so answer data cannot
  leak even by accident (checkpoint C1 proves this with a test).
"""

from rest_framework import serializers

from .models import Option, Question, Topic
from .services import validate_options


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name", "slug", "order", "description"]


class OptionWriteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=300)
    is_correct = serializers.BooleanField(default=False)
    order = serializers.IntegerField(required=False, min_value=0)


class OptionReadSerializer(serializers.ModelSerializer):
    """Student-facing option: text + display order only — NO is_correct."""

    class Meta:
        model = Option
        fields = ["id", "text", "order"]


class SeniorOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "text", "is_correct", "order"]


class StudentQuestionSerializer(serializers.ModelSerializer):
    """What a student sees. Deliberately excludes is_correct, explanation,
    author identity, and status internals."""

    topic = TopicSerializer(read_only=True)
    options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "topic",
            "type",
            "title",
            "body_markdown",
            "code_snippet",
            "difficulty",
            "base_points",
            "release_at",
            "close_at",
            "options",
        ]

    def get_options(self, obj):
        # Per-user deterministic shuffle (spec §6).
        request = self.context.get("request")
        user_id = request.user.id if request and request.user.is_authenticated else 0
        from .services import shuffled_options

        return OptionReadSerializer(shuffled_options(obj, user_id), many=True).data


class SeniorQuestionSerializer(serializers.ModelSerializer):
    """Full question for seniors: read shows options with is_correct;
    write accepts nested options and validates the spec rules."""

    topic = TopicSerializer(read_only=True)
    topic_id = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(), source="topic", write_only=True
    )
    options = SeniorOptionSerializer(many=True, read_only=True)
    options_input = OptionWriteSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Question
        fields = [
            "id",
            "topic",
            "topic_id",
            "type",
            "title",
            "body_markdown",
            "code_snippet",
            "difficulty",
            "explanation_markdown",
            "base_points",
            "release_at",
            "close_at",
            "status",
            "author",
            "options",
            "options_input",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at", "base_points"]

    author = serializers.StringRelatedField(read_only=True)

    def validate(self, attrs):
        # On create, options arrive as options_input; on update via options_input too.
        options = attrs.get("options_input")
        if options is not None:
            qtype = attrs.get("type") or getattr(self.instance, "type", None)
            validate_options(qtype, options)
        return attrs

    def create(self, validated_data):
        options = validated_data.pop("options_input", [])
        validated_data.pop("options", None)
        from .services import create_question

        # validated_data already carries `author` (injected by perform_create).
        return create_question(options=options, **validated_data)

    def update(self, instance, validated_data):
        options = validated_data.pop("options_input", None)
        validated_data.pop("options", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if options is not None:
            instance.options.all().delete()
            Option.objects.bulk_create(
                [
                    Option(
                        question=instance,
                        text=o["text"],
                        is_correct=o["is_correct"],
                        order=o.get("order", i),
                    )
                    for i, o in enumerate(options)
                ]
            )
        # Re-derive status from schedule on every save.
        from .services import _apply_status_timing

        _apply_status_timing(instance)
        instance.save(update_fields=["status"])
        return instance
