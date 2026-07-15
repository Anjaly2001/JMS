import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validate_manuscript_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in settings.ALLOWED_MANUSCRIPT_EXTENSIONS:
        raise ValidationError('Only PDF, DOC, and DOCX files are allowed for manuscripts.')
    if value.size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValidationError(f'File must be smaller than {settings.MAX_UPLOAD_SIZE_MB} MB.')


def validate_cover_image(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError('Only JPG and PNG images are allowed for cover images.')


class Journal(models.Model):
    """A journal published by the institution (e.g. 'Journal of Computer Science')."""

    title = models.CharField(max_length=255, unique=True)
    issn = models.CharField('ISSN', max_length=20, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to='covers/', blank=True, null=True, validators=[validate_cover_image]
    )
    editor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'profile__role': 'editor'},
        related_name='journals_edited',
        help_text='Assigned Editor responsible for this journal',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    @property
    def published_article_count(self):
        return Submission.objects.filter(journal=self, status=Submission.STATUS_PUBLISHED).count()


class Volume(models.Model):
    """A yearly volume of a journal (e.g. Volume 12, 2026)."""

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='volumes')
    number = models.PositiveIntegerField('Volume Number')
    year = models.PositiveIntegerField()

    class Meta:
        ordering = ['-year', '-number']
        unique_together = ['journal', 'number']

    def __str__(self):
        return f'{self.journal.title} - Volume {self.number} ({self.year})'


class Issue(models.Model):
    """An issue within a volume (e.g. Issue 2)."""

    volume = models.ForeignKey(Volume, on_delete=models.CASCADE, related_name='issues')
    issue_number = models.PositiveIntegerField()
    publish_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-volume__year', '-volume__number', '-issue_number']
        unique_together = ['volume', 'issue_number']

    def __str__(self):
        return f'{self.volume} - Issue {self.issue_number}'


class Submission(models.Model):
    """A manuscript submitted by an Author, moving through the editorial workflow."""

    STATUS_SUBMITTED = 'submitted'
    STATUS_SCREENING = 'screening'
    STATUS_UNDER_REVIEW = 'under_review'
    STATUS_REVISION_REQUESTED = 'revision_requested'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_PUBLISHED = 'published'

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_SCREENING, 'Screening'),
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_REVISION_REQUESTED, 'Revision Requested'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    # Bootstrap contextual colour used by templates for status badges.
    STATUS_BADGE = {
        STATUS_SUBMITTED: 'secondary',
        STATUS_SCREENING: 'info',
        STATUS_UNDER_REVIEW: 'primary',
        STATUS_REVISION_REQUESTED: 'warning',
        STATUS_ACCEPTED: 'success',
        STATUS_REJECTED: 'danger',
        STATUS_PUBLISHED: 'success',
    }

    submission_id = models.CharField(max_length=30, unique=True, blank=True, editable=False)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='submissions')
    issue = models.ForeignKey(
        Issue, on_delete=models.SET_NULL, null=True, blank=True, related_name='articles',
        help_text='Assigned once the article is scheduled for publication',
    )

    title = models.CharField(max_length=300)
    abstract = models.TextField()
    keywords = models.CharField(max_length=300, help_text='Comma-separated keywords')
    subject_area = models.CharField(max_length=150)
    co_authors = models.CharField(
        max_length=500, blank=True,
        help_text='Comma-separated names of co-authors (if any)',
    )
    corresponding_author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='submissions',
        limit_choices_to={'profile__role': 'author'},
    )
    manuscript_file = models.FileField(upload_to='manuscripts/', validators=[validate_manuscript_file])
    version_number = models.PositiveIntegerField(default=1)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    editor_decision_comment = models.TextField(blank=True)

    submission_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submission_date']

    def __str__(self):
        return f'{self.submission_id} - {self.title}'

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.submission_id:
            year = timezone.now().year
            self.submission_id = f'SUB-{year}-{self.pk:05d}'
            super().save(update_fields=['submission_id'])

    def get_status_badge(self):
        return self.STATUS_BADGE.get(self.status, 'secondary')

    @property
    def keyword_list(self):
        return [k.strip() for k in self.keywords.split(',') if k.strip()]


class Review(models.Model):
    """A peer review invitation/record for a submission."""

    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Invitation'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    RECOMMEND_ACCEPT = 'accept'
    RECOMMEND_MINOR = 'minor_revision'
    RECOMMEND_MAJOR = 'major_revision'
    RECOMMEND_REJECT = 'reject'

    RECOMMENDATION_CHOICES = [
        (RECOMMEND_ACCEPT, 'Accept'),
        (RECOMMEND_MINOR, 'Minor Revision'),
        (RECOMMEND_MAJOR, 'Major Revision'),
        (RECOMMEND_REJECT, 'Reject'),
    ]

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews',
        limit_choices_to={'profile__role': 'reviewer'},
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    recommendation = models.CharField(max_length=20, choices=RECOMMENDATION_CHOICES, blank=True)
    comments_to_author = models.TextField(blank=True)
    confidential_comments = models.TextField(blank=True, help_text='Visible to Editors only')

    due_date = models.DateField(null=True, blank=True)
    invited_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-invited_at']
        unique_together = ['submission', 'reviewer']

    def __str__(self):
        return f'Review of {self.submission.submission_id} by {self.reviewer.username}'
