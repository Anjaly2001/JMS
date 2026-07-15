<<<<<<< HEAD
from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """
    Extends the built-in Django User with the extra fields the Journal
    Management System needs: a role (for RBAC) and a few profile details.

    We use a one-to-one link to auth.User instead of a custom user model
    to keep authentication simple (Django's built-in login/auth is used
    as-is).
    """

    ROLE_ADMIN = 'admin'
    ROLE_EDITOR = 'editor'
    ROLE_REVIEWER = 'reviewer'
    ROLE_AUTHOR = 'author'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_EDITOR, 'Editor'),
        (ROLE_REVIEWER, 'Reviewer'),
        (ROLE_AUTHOR, 'Author'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_AUTHOR)
    affiliation = models.CharField(max_length=255, blank=True, help_text='College / Department')
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'

    @property
    def dashboard_url_name(self):
        return {
            self.ROLE_ADMIN: 'core:dashboard_admin',
            self.ROLE_EDITOR: 'core:dashboard_editor',
            self.ROLE_REVIEWER: 'core:dashboard_reviewer',
            self.ROLE_AUTHOR: 'core:dashboard_author',
        }[self.role]
=======
from django.db import models

# Create your models here.
>>>>>>> 6fbd5ab625782991d71a10edc3661e3dc19d8760
