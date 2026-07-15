from django.urls import path

from . import views

app_name = 'journal'

urlpatterns = [
    # Public browsing
    path('journals/', views.journal_public_list, name='journal_list'),
    path('journals/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('publications/', views.publication_list, name='publication_list'),
    path('publications/<int:pk>/', views.article_detail, name='article_detail'),

    # Journal CRUD (Administrator)
    path('manage/journals/', views.journal_manage_list, name='journal_manage_list'),
    path('manage/journals/add/', views.journal_create, name='journal_create'),
    path('manage/journals/<int:pk>/edit/', views.journal_update, name='journal_update'),
    path('manage/journals/<int:pk>/delete/', views.journal_delete, name='journal_delete'),
    path('manage/journals/<int:pk>/', views.journal_manage_detail, name='journal_manage_detail'),

    # Volume / Issue CRUD (Administrator or the journal's Editor)
    path('manage/journals/<int:journal_pk>/volumes/add/', views.volume_create, name='volume_create'),
    path('manage/volumes/<int:volume_pk>/issues/add/', views.issue_create, name='issue_create'),

    # Manuscript submission (Author)
    path('submissions/new/', views.submission_create, name='submission_create'),
    path('submissions/', views.submission_list, name='submission_list'),
    path('submissions/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('submissions/<int:pk>/upload-revision/', views.submission_upload_revision, name='submission_upload_revision'),

    # Editorial workflow (Editor / Administrator)
    path('submissions/<int:pk>/assign-reviewer/', views.assign_reviewer, name='assign_reviewer'),
    path('submissions/<int:pk>/decision/', views.editorial_decision, name='editorial_decision'),
    path('submissions/<int:pk>/publish/', views.publish_submission, name='publish_submission'),

    # Peer review (Reviewer) - specific paths (submit/download) must come
    # before the generic <str:action> pattern, or they'd be swallowed by it.
    path('reviews/<int:pk>/submit/', views.review_submit, name='review_submit'),
    path('reviews/<int:pk>/download/', views.review_download_manuscript, name='review_download_manuscript'),
    path('reviews/<int:pk>/<str:action>/', views.review_respond, name='review_respond'),
]
