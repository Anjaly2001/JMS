<<<<<<< HEAD
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import ProfileUpdateForm
from .models import Profile


class ProfileUpdateFormTests(TestCase):
    def test_role_field_is_available_on_profile_form(self):
        self.assertIn('role', ProfileUpdateForm.base_fields)


class AdminLoginTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin_user = self.User.objects.create_user(username='adminuser', password='secret123')
        Profile.objects.create(user=self.admin_user, role=Profile.ROLE_ADMIN)

        self.author_user = self.User.objects.create_user(username='authoruser', password='secret123')
        Profile.objects.create(user=self.author_user, role=Profile.ROLE_AUTHOR)

    def test_admin_login_allows_admin_user(self):
        response = self.client.post(reverse('accounts:admin_login'), {'username': 'adminuser', 'password': 'secret123'})
        self.assertRedirects(response, reverse('core:dashboard_admin'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_admin_login_rejects_non_admin_user(self):
        response = self.client.post(reverse('accounts:admin_login'), {'username': 'authoruser', 'password': 'secret123'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Only administrators can sign in here.')
=======
from django.test import TestCase

# Create your tests here.
>>>>>>> 6fbd5ab625782991d71a10edc3661e3dc19d8760
