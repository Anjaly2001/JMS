from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    """A simple, per-user notification record shown in the notification center."""

    CATEGORY_REGISTRATION = 'registration'
    CATEGORY_SUBMISSION = 'submission'
    CATEGORY_REVIEWER_INVITATION = 'reviewer_invitation'
    CATEGORY_EDITORIAL_DECISION = 'editorial_decision'
    CATEGORY_PUBLICATION = 'publication'

    CATEGORY_CHOICES = [
        (CATEGORY_REGISTRATION, 'Registration'),
        (CATEGORY_SUBMISSION, 'Submission'),
        (CATEGORY_REVIEWER_INVITATION, 'Reviewer Invitation'),
        (CATEGORY_EDITORIAL_DECISION, 'Editorial Decision'),
        (CATEGORY_PUBLICATION, 'Publication'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_category_display()} - {self.user.username}'
