from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication (using Django's built-in auth views + our templates)
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('admin-login/', views.admin_login, name='admin_login'),

    # Password change (logged-in users)
    path(
        'password-change/',
        auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'),
        name='password_change',
    ),
    path(
        'password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'),
        name='password_change_done',
    ),

    # Forgot password (public)
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
        name='password_reset_confirm',
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete',
    ),

    # Profile
    path('profile/', views.profile, name='profile'),

    # Administrator: user management
    path('users/', views.user_list, name='user_list'),
    path('settings/roles/', views.role_settings, name='role_settings'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/role/', views.user_role_update, name='user_role_update'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
]
