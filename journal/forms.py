from django import forms

from .models import Issue, Journal, Review, Submission, Volume


class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ['title', 'issn', 'description', 'cover_image', 'editor', 'is_active', 'categories']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'issn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2456-1290'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'editor': forms.Select(attrs={'class': 'form-select'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select', 'multiple': True}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class VolumeForm(forms.ModelForm):
    class Meta:
        model = Volume
        fields = ['number', 'year']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class IssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['issue_number', 'publish_date', 'is_published']
        widgets = {
            'issue_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'publish_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = [
            'journal', 'title', 'abstract', 'keywords', 'subject_area',
            'co_authors', 'manuscript_file',
        ]
        widgets = {
            'journal': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. AI, NLP, deep learning'}),
            'subject_area': forms.TextInput(attrs={'class': 'form-control'}),
            'co_authors': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional, comma-separated'}),
            'manuscript_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['journal'].queryset = self.fields['journal'].queryset.filter(is_active=True)


class RevisionUploadForm(forms.ModelForm):
    """A lighter form used when an Author uploads a revised manuscript version."""

    class Meta:
        model = Submission
        fields = ['manuscript_file']
        widgets = {'manuscript_file': forms.ClearableFileInput(attrs={'class': 'form-control'})}


class AssignReviewerForm(forms.Form):
    reviewer = forms.ModelChoiceField(
        queryset=None, label='Reviewer',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import User
        super().__init__(*args, **kwargs)
        self.fields['reviewer'].queryset = User.objects.filter(profile__role='reviewer', is_active=True)


class ReviewForm(forms.ModelForm):
    """Used by a Reviewer to submit their completed review."""

    class Meta:
        model = Review
        fields = ['recommendation', 'comments_to_author', 'confidential_comments']
        widgets = {
            'recommendation': forms.Select(attrs={'class': 'form-select'}),
            'comments_to_author': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'confidential_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EditorialDecisionForm(forms.Form):
    DECISION_CHOICES = [
        (Submission.STATUS_ACCEPTED, 'Accept'),
        (Submission.STATUS_REJECTED, 'Reject'),
        (Submission.STATUS_REVISION_REQUESTED, 'Request Revision'),
    ]
    decision = forms.ChoiceField(choices=DECISION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    comment = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Comment to Author',
    )
