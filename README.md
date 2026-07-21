# Journal Management System (JMS)

A Proof of Concept (POC) web application for managing academic journal
publishing at a university &mdash; built with Django 5, SQLite, and
Bootstrap 5.

This project implements manuscript submission, peer review, editorial
workflow, and publication for an academic institution, with role-based
dashboards for Administrators, Editors, Reviewers, and Authors.

---

## What's new in this revision

- **Unified navigation shell.** Logged-in users now stay inside the
  sidebar layout on every page, including the previously "public" pages
  (Journals, Publications, Search, Home). Clicking **Publications** from
  the sidebar no longer drops you into a different page layout.
- **Breadcrumbs** added throughout (e.g. `Dashboard > Manuscripts >
  SUB-2026-00001`), so deep pages always show how you got there and how
  to get back.
- **Consistent headings** restored on pages that had gone blank
  (Users, Journals, Manuscripts, Reports, Journal detail).
- **No more duplicate chrome**: the sidebar layout has no footer (the
  sidebar already ends in Logout); the public layout's footer carries a
  Logout button as a fallback for any page reached without a sidebar.
- **Security fix**: the self-service Profile page could previously edit
  your own `role` field, meaning any Author or Reviewer could grant
  themselves Administrator access. Role is now **only** changeable by an
  Administrator, via Users management.
- **Admin lockout protection**: an Administrator can no longer deactivate
  their own account, or change the role of the last remaining
  Administrator - the UI disables the action and shows why.
- **Fixed a broken Editor link**: the sidebar's "Journals" link for
  Editors pointed at an Administrator-only page; Editors can now view
  their own assigned journals (Admin-only actions like Add/Delete
  Journal remain hidden for them).
- Removed leftover, unused scaffolding (stray empty Django apps and a
  duplicate project folder) that had accumulated in the repo.

---

## 1. Features

- **Authentication**: login, registration (Author role), logout, forgot
  password, change password.
- **Role-Based Access Control (RBAC)**: Administrator, Editor, Reviewer,
  Author, plus anonymous public visitors who can browse published content.
- **Role-specific dashboards** with summary cards and quick actions.
- **Journal module**: CRUD for Journals, Volumes, and Issues.
- **Manuscript submission**: upload PDF/DOC/DOCX, abstract, keywords,
  subject area, co-authors; auto-generated Submission ID and version
  tracking.
- **Peer review workflow**: assign reviewers, accept/decline invitations,
  download manuscript, submit recommendation and comments.
- **Editorial workflow**: screen manuscripts, record decisions (Accept /
  Reject / Minor Revision / Major Revision), publish accepted articles.
- **Public publication pages**: browse journals and published articles,
  view abstracts, download PDFs &mdash; no login required.
- **Reports**: submission, journal, and reviewer reports, with an
  Excel/CSV export.
- **Notifications**: a simple in-app notification center covering
  registration, submission, reviewer invitation, editorial decision, and
  publication events.
- **Search**: journals, articles, and authors via basic ORM filtering.
- **User profile**: update details, change password, upload a photo.

## 2. Technology Stack

- Python 3.x, Django 5.0
- SQLite (models avoid SQLite-only features, so switching the `DATABASES`
  setting to PostgreSQL later is a small change)
- Bootstrap 5 + Bootstrap Icons (via CDN)
- Django Template Engine, Django ORM, Django ModelForms
- Django's built-in authentication and messages framework

No REST framework, service layers, or extra abstractions are used &mdash;
the project intentionally stays close to "vanilla" Django so it is easy to
read and explain in a code review.

## 3. Project Structure

```
JournalManagementSystem/
├── jms/                # Project settings, root URLs
├── accounts/           # Login, registration, profile, roles, user management
├── journal/            # Journals, volumes, issues, submissions, reviews
├── core/                # Home page, dashboards, search, reports, notifications
├── templates/           # base.html (unified shell), includes/, app templates
├── static/css/          # Custom Blue & White theme
├── media/                # Uploaded manuscripts, cover images, profile photos
├── requirements.txt
└── manage.py
```

Each app is deliberately narrow in scope:

- **accounts** &mdash; everything about *who* the user is (login, roles, profile).
- **journal** &mdash; everything about *journal content* (journals, submissions,
  reviews, publication).
- **core** &mdash; cross-cutting pages that don't belong to one specific model
  (home, dashboards, search, reports, notifications).

## 4. Database Models

| Model | Purpose |
|---|---|
| `accounts.Profile` | Extends `auth.User` with `role` and profile fields |
| `journal.Journal` | A published journal |
| `journal.Volume` | A yearly volume of a journal |
| `journal.Issue` | An issue within a volume |
| `journal.Submission` | A manuscript and its editorial status |
| `journal.Review` | A reviewer's invitation/record for a submission |
| `core.Notification` | A per-user notification |

## 5. Installation

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py makemigrations
python manage.py migrate

# 4. Create an administrator account
python manage.py createsuperuser

# 5. Run the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the public site and
`http://127.0.0.1:8000/admin/` for the Django admin panel.

### First-time setup after creating a superuser

Django's `createsuperuser` command creates an `auth.User` but not a JMS
`Profile`. After creating your superuser, either:

- Log into `/admin/` and add a `Profile` for that user with role
  **Administrator**, or
- Log in once at `/accounts/login/` — if no profile exists you'll be
  prompted to contact an administrator, so creating the Profile via
  `/admin/` first is the quickest path.

From there, use the **Users** page (as an Administrator) to create Editor
and Reviewer accounts. Authors can self-register at `/accounts/register/`.

### Optional: load sample data

A fixture with a demo Administrator, Editor, Reviewer, Author, one
Journal (with a Volume/Issue), and one published Submission is included
for convenience:

```bash
python manage.py loaddata core/fixtures/sample_data.json
```

Demo accounts (all created with role and password `<username>12345`,
e.g. `admin` / `admin12345`):

| Username | Role | Password |
|---|---|---|
| `admin` | Administrator | `admin12345` |
| `editor1` | Editor | `editor12345` |
| `reviewer1` | Reviewer | `reviewer12345` |
| `author1` | Author | `author12345` |

## 6. Typical Workflow (Demo Script)

1. **Administrator** creates a Journal and assigns an Editor.
2. **Administrator** adds a Volume and Issue to the Journal.
3. **Author** registers, logs in, and submits a manuscript to the Journal.
4. **Editor** assigns a Reviewer to the submission.
5. **Reviewer** accepts the invitation, downloads the manuscript, and
   submits a review with a recommendation.
6. **Editor** records an editorial decision (Accept / Reject / Revision).
7. If accepted, the **Editor** publishes the submission, optionally
   assigning it to an Issue.
8. The article now appears on the public **Articles** page and the
   journal's detail page for anyone to read and download.

Notifications are created automatically at each step and appear in the
notification bell / center for the relevant user.

## 7. Security Notes (POC scope)

- CSRF protection is enabled via Django's default middleware.
- Role-based authorization is enforced with `@login_required` and
  `@user_passes_test` decorators on every protected view.
- **Role changes are Administrator-only.** A logged-in user's own
  Profile page cannot edit their role; only the Users management page
  (`/accounts/users/`) can promote or demote an account. An
  Administrator also can't deactivate their own account or demote the
  last remaining Administrator, to avoid locking everyone out.
- A dedicated `/accounts/admin-login/` page exists for Administrator
  sign-in; it rejects non-administrator credentials even if they're
  otherwise valid.
- Passwords are hashed using Django's default password hashers.
- Manuscript and image uploads are validated by file extension and size
  (see `journal/models.py` and `settings.py`).
- `SECRET_KEY` and `DEBUG=True` in `jms/settings.py` are fine for local
  development only — replace them (via environment variables) before any
  real deployment.

## 8. Notes on Scope

This is a POC, so a few things are intentionally simplified:

- Co-authors are stored as a comma-separated text field rather than a
  separate model, to avoid an extra join for a field that's read-only in
  this workflow.
- The "Excel export" on the Reports page produces a CSV file, which Excel
  opens natively; a full `.xlsx` (openpyxl) or PDF (reportlab) export can
  be added later without changing the report page itself.
- Email sending (e.g. for password reset) uses Django's console/dummy
  backend by default in development — configure `EMAIL_BACKEND` in
  `settings.py` to send real emails.
