from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import ProfileUpdateForm
from .models import Profile


class ProfileUpdateFormTests(TestCase):
    def test_role_field_is_not_available_on_profile_form(self):
        """
        Role must never be editable via the self-service profile form -
        otherwise any logged-in user could grant themselves a higher-
        privilege role. Role changes are only allowed through the
        Administrator-only accounts:user_role_update view.
        """
        self.assertNotIn('role', ProfileUpdateForm.base_fields)

    def test_posting_a_role_to_the_profile_view_does_not_change_it(self):
        """Even if a role value is smuggled into the POST body, it must be ignored."""
        User = get_user_model()
        author = User.objects.create_user(username='authoruser2', password='secret123')
        Profile.objects.create(user=author, role=Profile.ROLE_AUTHOR)

        self.client.login(username='authoruser2', password='secret123')
        self.client.post(reverse('accounts:profile'), {
            'first_name': 'Test', 'last_name': 'User', 'email': 'a@example.com',
            'affiliation': '', 'phone': '', 'role': Profile.ROLE_ADMIN,
        })
        author.profile.refresh_from_db()
        self.assertEqual(author.profile.role, Profile.ROLE_AUTHOR)


class ProfileViewTests(TestCase):
    def test_profile_view_creates_missing_profile_for_existing_user(self):
        User = get_user_model()
        user = User.objects.create_user(username='missingprofile', password='secret123')

        self.assertFalse(Profile.objects.filter(user=user).exists())

        self.client.login(username='missingprofile', password='secret123')
        response = self.client.get(reverse('accounts:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.role, Profile.ROLE_AUTHOR)


class AdminSelfLockoutTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin_user = self.User.objects.create_user(username='soleadmin', password='secret123')
        Profile.objects.create(user=self.admin_user, role=Profile.ROLE_ADMIN)
        self.client.login(username='soleadmin', password='secret123')

    def test_admin_cannot_deactivate_own_account(self):
        self.client.post(reverse('accounts:user_toggle_active', args=[self.admin_user.pk]))
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_last_admin_cannot_be_demoted(self):
        self.client.post(reverse('accounts:user_role_update', args=[self.admin_user.pk]), {
            'role': Profile.ROLE_AUTHOR,
        })
        self.admin_user.profile.refresh_from_db()
        self.assertEqual(self.admin_user.profile.role, Profile.ROLE_ADMIN)


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
