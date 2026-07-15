import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Profile
from journal.models import Journal, Review, Submission

from .models import Notification


# ---------------------------------------------------------------------------
# Public landing page
# ---------------------------------------------------------------------------

def home(request):
    featured_journals = Journal.objects.filter(is_active=True)[:6]
    latest_articles = Submission.objects.filter(
        status=Submission.STATUS_PUBLISHED
    ).select_related('journal')[:6]
    return render(request, 'home.html', {
        'featured_journals': featured_journals,
        'latest_articles': latest_articles,
    })


# ---------------------------------------------------------------------------
# Dashboard router: sends the logged-in user to their role-specific dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Your account has no profile / role assigned. Please contact an administrator.')
        return redirect('core:home')
    return redirect(request.user.profile.dashboard_url_name)


def _role_required(role):
    def check(user):
        return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == role
    return check


@user_passes_test(_role_required(Profile.ROLE_ADMIN), login_url='core:dashboard')
def dashboard_admin(request):
    context = {
        'total_users': User.objects.count(),
        'total_journals': Journal.objects.count(),
        'total_manuscripts': Submission.objects.count(),
        'total_reviews': Review.objects.count(),
        'published_articles': Submission.objects.filter(status=Submission.STATUS_PUBLISHED).count(),
        'recent_submissions': Submission.objects.select_related('journal')[:5],
    }
    return render(request, 'core/dashboard_admin.html', context)


@user_passes_test(_role_required(Profile.ROLE_EDITOR), login_url='core:dashboard')
def dashboard_editor(request):
    journal_submissions = Submission.objects.filter(journal__editor=request.user)
    context = {
        'new_submissions': journal_submissions.filter(status=Submission.STATUS_SUBMITTED).count(),
        'under_review': journal_submissions.filter(status=Submission.STATUS_UNDER_REVIEW).count(),
        'revision_requested': journal_submissions.filter(status=Submission.STATUS_REVISION_REQUESTED).count(),
        'accepted': journal_submissions.filter(status=Submission.STATUS_ACCEPTED).count(),
        'rejected': journal_submissions.filter(status=Submission.STATUS_REJECTED).count(),
        'recent_submissions': journal_submissions.select_related('journal')[:8],
    }
    return render(request, 'core/dashboard_editor.html', context)


@user_passes_test(_role_required(Profile.ROLE_REVIEWER), login_url='core:dashboard')
def dashboard_reviewer(request):
    my_reviews = Review.objects.filter(reviewer=request.user)
    context = {
        'pending_invitations': my_reviews.filter(status=Review.STATUS_PENDING).count(),
        'assigned_reviews': my_reviews.filter(status=Review.STATUS_ACCEPTED).count(),
        'completed_reviews': my_reviews.filter(status=Review.STATUS_COMPLETED).count(),
        'reviews': my_reviews.select_related('submission', 'submission__journal')[:10],
    }
    return render(request, 'core/dashboard_reviewer.html', context)


@user_passes_test(_role_required(Profile.ROLE_AUTHOR), login_url='core:dashboard')
def dashboard_author(request):
    my_submissions = Submission.objects.filter(corresponding_author=request.user)
    context = {
        'my_submissions_count': my_submissions.count(),
        'under_review': my_submissions.filter(status=Submission.STATUS_UNDER_REVIEW).count(),
        'accepted': my_submissions.filter(status=Submission.STATUS_ACCEPTED).count(),
        'revision_requested': my_submissions.filter(status=Submission.STATUS_REVISION_REQUESTED).count(),
        'published': my_submissions.filter(status=Submission.STATUS_PUBLISHED).count(),
        'submissions': my_submissions.select_related('journal')[:10],
    }
    return render(request, 'core/dashboard_author.html', context)


# ---------------------------------------------------------------------------
# Search (public): journals, articles, authors via simple ORM filtering
# ---------------------------------------------------------------------------

def search(request):
    query = request.GET.get('q', '').strip()
    journals = articles = authors = None

    if query:
        journals = Journal.objects.filter(Q(title__icontains=query) | Q(description__icontains=query), is_active=True)
        articles = Submission.objects.filter(
            Q(title__icontains=query) | Q(keywords__icontains=query) | Q(abstract__icontains=query),
            status=Submission.STATUS_PUBLISHED,
        ).select_related('journal')
        authors = User.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(username__icontains=query),
            profile__role=Profile.ROLE_AUTHOR,
        )

    return render(request, 'core/search.html', {
        'query': query, 'journals': journals, 'articles': articles, 'authors': authors,
    })


# ---------------------------------------------------------------------------
# Reports (Administrator only)
# ---------------------------------------------------------------------------

@user_passes_test(_role_required(Profile.ROLE_ADMIN), login_url='core:dashboard')
def reports(request):
    submission_status_counts = Submission.objects.values('status').annotate(total=Count('id'))
    journal_report = Journal.objects.annotate(submission_count=Count('submissions'))
    reviewer_report = User.objects.filter(profile__role=Profile.ROLE_REVIEWER).annotate(
        review_count=Count('reviews')
    )
    total_decided = Submission.objects.filter(
        status__in=[Submission.STATUS_ACCEPTED, Submission.STATUS_REJECTED, Submission.STATUS_PUBLISHED]
    ).count()
    total_accepted = Submission.objects.filter(
        status__in=[Submission.STATUS_ACCEPTED, Submission.STATUS_PUBLISHED]
    ).count()
    acceptance_rate = round((total_accepted / total_decided) * 100, 1) if total_decided else 0

    return render(request, 'core/reports.html', {
        'submission_status_counts': submission_status_counts,
        'journal_report': journal_report,
        'reviewer_report': reviewer_report,
        'acceptance_rate': acceptance_rate,
        'total_decided': total_decided,
        'total_accepted': total_accepted,
    })


@user_passes_test(_role_required(Profile.ROLE_ADMIN), login_url='core:dashboard')
def export_submissions_csv(request):
    """Simple 'Excel export' - a CSV file, which Excel opens natively."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="submission_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Submission ID', 'Title', 'Journal', 'Author', 'Status', 'Submitted On'])
    for s in Submission.objects.select_related('journal', 'corresponding_author'):
        writer.writerow([
            s.submission_id, s.title, s.journal.title,
            s.corresponding_author.get_full_name() or s.corresponding_author.username,
            s.get_status_display(), s.submission_date.strftime('%Y-%m-%d'),
        ])
    return response


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifications})
