from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Profile
from core.models import Notification

from .forms import (
    AssignReviewerForm,
    EditorialDecisionForm,
    IssueForm,
    JournalForm,
    ReviewForm,
    RevisionUploadForm,
    SubmissionForm,
    VolumeForm,
)
from .models import Issue, Journal, Review, Submission, Volume

PAGE_SIZE = 10


# ---------------------------------------------------------------------------
# Role check helpers (kept simple on purpose - no permissions framework).
# ---------------------------------------------------------------------------

def _role(user):
    return getattr(getattr(user, 'profile', None), 'role', None)


def is_admin(user):
    return user.is_authenticated and _role(user) == Profile.ROLE_ADMIN


def is_editor(user):
    return user.is_authenticated and _role(user) == Profile.ROLE_EDITOR


def is_admin_or_editor(user):
    return user.is_authenticated and _role(user) in (Profile.ROLE_ADMIN, Profile.ROLE_EDITOR)


def is_reviewer(user):
    return user.is_authenticated and _role(user) == Profile.ROLE_REVIEWER


def is_author(user):
    return user.is_authenticated and _role(user) == Profile.ROLE_AUTHOR


# ---------------------------------------------------------------------------
# Public: browse journals & published articles (no login required)
# ---------------------------------------------------------------------------

def journal_public_list(request):
    journals = Journal.objects.filter(is_active=True)
    return render(request, 'journal/journal_list.html', {'journals': journals})


def journal_detail(request, pk):
    journal = get_object_or_404(Journal, pk=pk, is_active=True)
    volumes = journal.volumes.prefetch_related('issues').all()
    published_articles = Submission.objects.filter(
        journal=journal, status=Submission.STATUS_PUBLISHED
    ).order_by('-submission_date')
    return render(request, 'journal/journal_detail.html', {
        'journal': journal, 'volumes': volumes, 'published_articles': published_articles,
    })


def publication_list(request):
    articles = Submission.objects.filter(status=Submission.STATUS_PUBLISHED).select_related('journal')
    paginator = Paginator(articles, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'journal/publication_list.html', {'page_obj': page_obj})


def article_detail(request, pk):
    article = get_object_or_404(Submission, pk=pk, status=Submission.STATUS_PUBLISHED)
    return render(request, 'journal/article_detail.html', {'article': article})


# ---------------------------------------------------------------------------
# Journal CRUD (Administrator)
# ---------------------------------------------------------------------------

@user_passes_test(is_admin, login_url='core:dashboard')
def journal_manage_list(request):
    journals = Journal.objects.all()
    return render(request, 'journal/journal_manage_list.html', {'journals': journals})


@user_passes_test(is_admin, login_url='core:dashboard')
def journal_create(request):
    if request.method == 'POST':
        form = JournalForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Journal created successfully.')
            return redirect('journal:journal_manage_list')
    else:
        form = JournalForm()
    return render(request, 'journal/journal_form.html', {'form': form, 'title': 'Add Journal'})


@user_passes_test(is_admin, login_url='core:dashboard')
def journal_update(request, pk):
    journal = get_object_or_404(Journal, pk=pk)
    if request.method == 'POST':
        form = JournalForm(request.POST, request.FILES, instance=journal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Journal updated successfully.')
            return redirect('journal:journal_manage_list')
    else:
        form = JournalForm(instance=journal)
    return render(request, 'journal/journal_form.html', {'form': form, 'title': 'Edit Journal'})


@user_passes_test(is_admin, login_url='core:dashboard')
def journal_delete(request, pk):
    journal = get_object_or_404(Journal, pk=pk)
    if request.method == 'POST':
        journal.delete()
        messages.success(request, 'Journal deleted.')
        return redirect('journal:journal_manage_list')
    return render(request, 'journal/confirm_delete.html', {'object': journal, 'type_label': 'journal'})


# ---------------------------------------------------------------------------
# Volume / Issue CRUD (Administrator or the journal's assigned Editor)
# ---------------------------------------------------------------------------

def _can_manage_journal(user, journal):
    return is_admin(user) or (is_editor(user) and journal.editor_id == user.id)


@login_required
def volume_create(request, journal_pk):
    journal = get_object_or_404(Journal, pk=journal_pk)
    if not _can_manage_journal(request.user, journal):
        messages.error(request, 'You do not have permission to manage this journal.')
        return redirect('journal:journal_detail', pk=journal.pk)

    if request.method == 'POST':
        form = VolumeForm(request.POST)
        if form.is_valid():
            volume = form.save(commit=False)
            volume.journal = journal
            volume.save()
            messages.success(request, 'Volume added.')
            return redirect('journal:journal_manage_detail', pk=journal.pk)
    else:
        form = VolumeForm()
    return render(request, 'journal/volume_form.html', {'form': form, 'journal': journal})


@login_required
def issue_create(request, volume_pk):
    volume = get_object_or_404(Volume, pk=volume_pk)
    if not _can_manage_journal(request.user, volume.journal):
        messages.error(request, 'You do not have permission to manage this journal.')
        return redirect('journal:journal_detail', pk=volume.journal.pk)

    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.volume = volume
            issue.save()
            messages.success(request, 'Issue added.')
            return redirect('journal:journal_manage_detail', pk=volume.journal.pk)
    else:
        form = IssueForm()
    return render(request, 'journal/issue_form.html', {'form': form, 'volume': volume})


@login_required
def journal_manage_detail(request, pk):
    journal = get_object_or_404(Journal, pk=pk)
    if not _can_manage_journal(request.user, journal):
        messages.error(request, 'You do not have permission to manage this journal.')
        return redirect('journal:journal_detail', pk=journal.pk)
    volumes = journal.volumes.prefetch_related('issues').all()
    return render(request, 'journal/journal_manage_detail.html', {'journal': journal, 'volumes': volumes})


# ---------------------------------------------------------------------------
# Manuscript submission (Author)
# ---------------------------------------------------------------------------

@user_passes_test(is_author, login_url='core:dashboard')
def submission_create(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.corresponding_author = request.user
            submission.save()
            Notification.objects.create(
                user=request.user,
                category=Notification.CATEGORY_SUBMISSION,
                message=f'Your manuscript "{submission.title}" was submitted successfully ({submission.submission_id}).',
            )
            messages.success(request, f'Manuscript submitted. Your submission ID is {submission.submission_id}.')
            return redirect('journal:submission_detail', pk=submission.pk)
    else:
        form = SubmissionForm()
    return render(request, 'journal/submission_form.html', {'form': form})


@login_required
def submission_list(request):
    """Shows a different queryset depending on the logged-in user's role."""
    role = _role(request.user)
    status_filter = request.GET.get('status', '')

    if role == Profile.ROLE_AUTHOR:
        submissions = Submission.objects.filter(corresponding_author=request.user)
    elif role == Profile.ROLE_EDITOR:
        submissions = Submission.objects.filter(journal__editor=request.user)
    elif role == Profile.ROLE_ADMIN:
        submissions = Submission.objects.all()
    elif role == Profile.ROLE_REVIEWER:
        review_submission_ids = Review.objects.filter(reviewer=request.user).values_list('submission_id', flat=True)
        submissions = Submission.objects.filter(pk__in=review_submission_ids)
    else:
        submissions = Submission.objects.none()

    if status_filter:
        submissions = submissions.filter(status=status_filter)

    submissions = submissions.select_related('journal', 'corresponding_author')
    paginator = Paginator(submissions, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'journal/submission_list.html', {
        'page_obj': page_obj,
        'status_choices': Submission.STATUS_CHOICES,
        'status_filter': status_filter,
    })


def _can_view_submission(user, submission):
    role = _role(user)
    if role == Profile.ROLE_ADMIN:
        return True
    if role == Profile.ROLE_EDITOR:
        return submission.journal.editor_id == user.id
    if role == Profile.ROLE_AUTHOR:
        return submission.corresponding_author_id == user.id
    if role == Profile.ROLE_REVIEWER:
        return submission.reviews.filter(reviewer=user).exists()
    return False


@login_required
def submission_detail(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    if not _can_view_submission(request.user, submission):
        messages.error(request, 'You do not have permission to view this submission.')
        return redirect('journal:submission_list')

    role = _role(request.user)
    reviews = submission.reviews.select_related('reviewer')
    my_review = reviews.filter(reviewer=request.user).first() if role == Profile.ROLE_REVIEWER else None

    context = {
        'submission': submission,
        'reviews': reviews if role in (Profile.ROLE_ADMIN, Profile.ROLE_EDITOR) else None,
        'my_review': my_review,
        'can_manage': role in (Profile.ROLE_ADMIN, Profile.ROLE_EDITOR) and (
            role == Profile.ROLE_ADMIN or submission.journal.editor_id == request.user.id
        ),
        'is_owner': submission.corresponding_author_id == request.user.id,
    }
    return render(request, 'journal/submission_detail.html', context)


@login_required
def submission_upload_revision(request, pk):
    submission = get_object_or_404(Submission, pk=pk, corresponding_author=request.user)
    if submission.status != Submission.STATUS_REVISION_REQUESTED:
        messages.error(request, 'This submission is not awaiting a revision.')
        return redirect('journal:submission_detail', pk=pk)

    if request.method == 'POST':
        form = RevisionUploadForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.version_number += 1
            submission.status = Submission.STATUS_UNDER_REVIEW
            submission.save()
            messages.success(request, 'Revised manuscript uploaded.')
            return redirect('journal:submission_detail', pk=pk)
    else:
        form = RevisionUploadForm(instance=submission)
    return render(request, 'journal/revision_form.html', {'form': form, 'submission': submission})


# ---------------------------------------------------------------------------
# Editorial workflow (Editor / Administrator)
# ---------------------------------------------------------------------------

@login_required
def assign_reviewer(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    if not (is_admin(request.user) or (is_editor(request.user) and submission.journal.editor_id == request.user.id)):
        messages.error(request, 'You do not have permission to assign reviewers for this submission.')
        return redirect('journal:submission_detail', pk=pk)

    if request.method == 'POST':
        form = AssignReviewerForm(request.POST)
        if form.is_valid():
            reviewer = form.cleaned_data['reviewer']
            Review.objects.get_or_create(
                submission=submission, reviewer=reviewer,
                defaults={'due_date': form.cleaned_data['due_date']},
            )
            if submission.status == Submission.STATUS_SUBMITTED:
                submission.status = Submission.STATUS_SCREENING
                submission.save(update_fields=['status'])
            Notification.objects.create(
                user=reviewer,
                category=Notification.CATEGORY_REVIEWER_INVITATION,
                message=f'You have been invited to review "{submission.title}" ({submission.submission_id}).',
            )
            messages.success(request, f'{reviewer.username} invited to review this submission.')
            return redirect('journal:submission_detail', pk=pk)
    else:
        form = AssignReviewerForm()
    return render(request, 'journal/assign_reviewer_form.html', {'form': form, 'submission': submission})


@login_required
def editorial_decision(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    if not (is_admin(request.user) or (is_editor(request.user) and submission.journal.editor_id == request.user.id)):
        messages.error(request, 'You do not have permission to record a decision for this submission.')
        return redirect('journal:submission_detail', pk=pk)

    if request.method == 'POST':
        form = EditorialDecisionForm(request.POST)
        if form.is_valid():
            submission.status = form.cleaned_data['decision']
            submission.editor_decision_comment = form.cleaned_data['comment']
            submission.save(update_fields=['status', 'editor_decision_comment'])
            Notification.objects.create(
                user=submission.corresponding_author,
                category=Notification.CATEGORY_EDITORIAL_DECISION,
                message=(
                    f'A decision has been recorded for "{submission.title}": '
                    f'{submission.get_status_display()}.'
                ),
            )
            messages.success(request, 'Editorial decision recorded and the author has been notified.')
            return redirect('journal:submission_detail', pk=pk)
    else:
        form = EditorialDecisionForm()
    return render(request, 'journal/editorial_decision_form.html', {'form': form, 'submission': submission})


@login_required
def publish_submission(request, pk):
    """Editor/Admin: mark an accepted submission as Published and attach it to an Issue."""
    submission = get_object_or_404(Submission, pk=pk, status=Submission.STATUS_ACCEPTED)
    if not (is_admin(request.user) or (is_editor(request.user) and submission.journal.editor_id == request.user.id)):
        messages.error(request, 'You do not have permission to publish this submission.')
        return redirect('journal:submission_detail', pk=pk)

    issues = Issue.objects.filter(volume__journal=submission.journal)
    if request.method == 'POST':
        issue_id = request.POST.get('issue')
        submission.issue_id = issue_id or None
        submission.status = Submission.STATUS_PUBLISHED
        submission.save(update_fields=['issue', 'status'])
        Notification.objects.create(
            user=submission.corresponding_author,
            category=Notification.CATEGORY_PUBLICATION,
            message=f'Your article "{submission.title}" has been published!',
        )
        messages.success(request, 'Submission published.')
        return redirect('journal:submission_detail', pk=pk)

    return render(request, 'journal/publish_form.html', {'submission': submission, 'issues': issues})


# ---------------------------------------------------------------------------
# Peer review (Reviewer)
# ---------------------------------------------------------------------------

@user_passes_test(is_reviewer, login_url='core:dashboard')
def review_respond(request, pk, action):
    """Reviewer accepts or declines a review invitation."""
    review = get_object_or_404(Review, pk=pk, reviewer=request.user)
    if action == 'accept':
        review.status = Review.STATUS_ACCEPTED
        messages.success(request, 'Review invitation accepted.')
    elif action == 'decline':
        review.status = Review.STATUS_DECLINED
        messages.info(request, 'Review invitation declined.')
    review.save(update_fields=['status'])
    return redirect('journal:submission_detail', pk=review.submission_id)


@user_passes_test(is_reviewer, login_url='core:dashboard')
def review_submit(request, pk):
    review = get_object_or_404(Review, pk=pk, reviewer=request.user)
    if review.status not in (Review.STATUS_ACCEPTED,):
        messages.error(request, 'Accept the review invitation before submitting your review.')
        return redirect('journal:submission_detail', pk=review.submission_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.status = Review.STATUS_COMPLETED
            from django.utils import timezone
            review.submitted_at = timezone.now()
            review.save()
            if review.submission.status == Submission.STATUS_SCREENING:
                review.submission.status = Submission.STATUS_UNDER_REVIEW
                review.submission.save(update_fields=['status'])
            messages.success(request, 'Review submitted. Thank you!')
            return redirect('journal:submission_list')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'journal/review_form.html', {'form': form, 'review': review})


@login_required
def review_download_manuscript(request, pk):
    """Convenience redirect so reviewer templates have one clear download link."""
    review = get_object_or_404(Review, pk=pk, reviewer=request.user)
    return redirect(review.submission.manuscript_file.url)
