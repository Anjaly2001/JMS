from django.contrib import admin

from .models import Issue, Journal, Review, Submission, Volume


class VolumeInline(admin.TabularInline):
    model = Volume
    extra = 0


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ['title', 'issn', 'editor', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['title', 'issn']
    inlines = [VolumeInline]


class IssueInline(admin.TabularInline):
    model = Issue
    extra = 0


@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    list_display = ['journal', 'number', 'year']
    list_filter = ['journal']
    inlines = [IssueInline]


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['volume', 'issue_number', 'publish_date', 'is_published']
    list_filter = ['is_published']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['submission_id', 'title', 'journal', 'corresponding_author', 'status', 'submission_date']
    list_filter = ['status', 'journal']
    search_fields = ['submission_id', 'title', 'corresponding_author__username']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['submission', 'reviewer', 'status', 'recommendation', 'due_date']
    list_filter = ['status', 'recommendation']
