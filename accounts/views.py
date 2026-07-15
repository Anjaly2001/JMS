from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Notification

from .forms import (
    AdminLoginForm,
    AdminUserCreateForm,
    AdminUserRoleForm,
    ProfileUpdateForm,
    RegistrationForm,
    UserUpdateForm,
)
from .models import Profile


def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == Profile.ROLE_ADMIN


def admin_login(request):
    """Dedicated login page for administrators only."""
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('core:dashboard_admin')
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not is_admin(user):
                form.add_error(None, 'Only administrators can sign in here.')
            else:
                login(request, user)
                messages.success(request, 'Welcome back, administrator.')
                return redirect('core:dashboard_admin')
    else:
        form = AdminLoginForm()

    return render(request, 'accounts/admin_login.html', {'form': form})


def register(request):
    """Public self-registration. New accounts are always given the Author role."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            Notification.objects.create(
                user=user,
                category=Notification.CATEGORY_REGISTRATION,
                message='Welcome to the Journal Management System! Your author account is ready.',
            )
            messages.success(request, 'Registration successful. Welcome!')
            return redirect('core:dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    """Lets any logged-in user view/update their profile and change photo."""
    user_form = UserUpdateForm(instance=request.user)
    profile_form = ProfileUpdateForm(instance=request.user.profile)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@user_passes_test(is_admin, login_url='core:dashboard')
def user_list(request):
    """Administrator: manage all user accounts and their roles."""
    users = User.objects.select_related('profile').order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})


@user_passes_test(is_admin, login_url='core:dashboard')
def role_settings(request):
    """Administrator: manage user roles from a dedicated settings page."""
    users = User.objects.select_related('profile').order_by('-date_joined')
    return render(request, 'accounts/role_settings.html', {'users': users})


@user_passes_test(is_admin, login_url='core:dashboard')
def user_create(request):
    """Administrator: create Editor / Reviewer / Administrator accounts."""
    if request.method == 'POST':
        form = AdminUserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User account created successfully.')
            return redirect('accounts:user_list')
    else:
        form = AdminUserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form})


@user_passes_test(is_admin, login_url='core:dashboard')
def user_role_update(request, pk):
    """Administrator: change a user's role."""
    target_profile = get_object_or_404(Profile, user_id=pk)
    if request.method == 'POST':
        form = AdminUserRoleForm(request.POST, instance=target_profile)
        if form.is_valid():
            form.save()
            messages.success(request, f'Role updated for {target_profile.user.username}.')
            return redirect('accounts:user_list')
    else:
        form = AdminUserRoleForm(instance=target_profile)
    return render(request, 'accounts/user_role_form.html', {'form': form, 'target_user': target_profile.user})


@user_passes_test(is_admin, login_url='core:dashboard')
def user_toggle_active(request, pk):
    """Administrator: activate/deactivate (lock) a user account."""
    target_user = get_object_or_404(User, pk=pk)
    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])
    state = 'activated' if target_user.is_active else 'deactivated'
    messages.success(request, f'Account for {target_user.username} was {state}.')
    return redirect('accounts:user_list')
