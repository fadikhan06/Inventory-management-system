"""Global template context processor — makes shop/notifications available everywhere."""
from inventory.models import Notification


def global_context(request):
    """Inject current shop and unread notification count into every template."""
    if not request.user.is_authenticated:
        return {}

    try:
        profile = request.user.profile
        shop = profile.shop
    except Exception:
        shop = None

    unread_count = 0
    if shop:
        unread_count = Notification.objects.filter(shop=shop, is_read=False).count()

    return {
        'current_shop': shop,
        'unread_notifications': unread_count,
        'user_role': getattr(getattr(request.user, 'profile', None), 'role', 'staff'),
    }
