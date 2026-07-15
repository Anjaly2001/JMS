from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class AdminLoginForm(AuthenticationForm):
    """Admin-only login form that uses the same credentials but restricts access to administrators."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class RegistrationForm(UserCreationForm):
    """
    Registration form for public visitors.

    Only the Author role is offered on public sign-up. Administrator,
    Editor, and Reviewer accounts are created/promoted by an
    Administrator from the Users management page, which keeps the
    Role-Based Access Control meaningful.
    """

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    affiliation = forms.CharField(
        max_length=255, required=False,
        help_text='Your college / department (optional)',
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                role=Profile.ROLE_AUTHOR,
                affiliation=self.cleaned_data.get('affiliation', ''),
            )
        return user


class UserUpdateForm(forms.ModelForm):
    """Lets a logged-in user update their basic account details."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """Lets a logged-in user update their profile details / photo."""

    class Meta:
        model = Profile
        fields = ['role', 'affiliation', 'phone', 'photo']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'affiliation': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class AdminUserCreateForm(UserCreationForm):
    """Used by Administrators to create Editor / Reviewer / Admin accounts."""

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'role':
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Profile.objects.create(user=user, role=self.cleaned_data['role'])
        return user


class AdminUserRoleForm(forms.ModelForm):
    """Used by Administrators to change an existing user's role or lock the account."""

    class Meta:
        model = Profile
        fields = ['role']
        widgets = {'role': forms.Select(attrs={'class': 'form-select'})}
