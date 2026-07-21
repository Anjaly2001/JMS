from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/editor/', views.dashboard_editor, name='dashboard_editor'),
    path('dashboard/reviewer/', views.dashboard_reviewer, name='dashboard_reviewer'),
    path('dashboard/author/', views.dashboard_author, name='dashboard_author'),
    path('search/', views.search, name='search'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/csv/', views.export_submissions_csv, name='export_submissions_csv'),
    path('notifications/', views.notification_list, name='notifications'),
]
