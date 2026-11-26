from django.contrib import admin

from .models import CodeProblem, CodeSubmission, TestCase


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 1


@admin.register(CodeProblem)
class CodeProblemAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "difficulty", "points", "is_published", "created_by")
    list_filter = ("difficulty", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [TestCaseInline]


@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "problem", "status", "score", "is_flagged_similar", "created_at")
    list_filter = ("status", "is_flagged_similar")
    readonly_fields = ("code", "results", "created_at")
