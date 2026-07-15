def sidebar_context(request):
    """
    Makes a few small, frequently-needed values available to every template
    without every view having to pass them explicitly:
      - the current user's role (or None for anonymous / public visitors)
      - how many unread notifications they have (for the navbar bell icon)
    """
    role = None
    unread_notifications = 0

    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        role = request.user.profile.role
        unread_notifications = request.user.notifications.filter(is_read=False).count()

    return {
        'current_role': role,
        'unread_notifications': unread_notifications,
    }
