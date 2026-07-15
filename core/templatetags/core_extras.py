from django import template

register = template.Library()


@register.filter
def status_badge(status_code):
    """Returns a Bootstrap contextual class for a Submission status code."""
    mapping = {
        'submitted': 'secondary',
        'screening': 'info',
        'under_review': 'primary',
        'revision_requested': 'warning',
        'accepted': 'success',
        'rejected': 'danger',
        'published': 'success',
        'pending': 'secondary',
        'declined': 'danger',
        'completed': 'success',
    }
    return mapping.get(status_code, 'secondary')
