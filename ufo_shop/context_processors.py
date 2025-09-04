from django.db.models import Sum
from .models import Order


def cart_info(request):
    """Provide cart item count for authenticated users.
    Returns cart_count: sum of item amounts in IN_CART order, else 0.
    """
    cart_count = 0
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            cart = Order.objects.get(user=user, status=Order.Status.IN_CART)
            cart_count = cart.orderitem_set.aggregate(total=Sum('amount'))['total'] or 0
        except Order.DoesNotExist:
            cart_count = 0
    return {'cart_count': cart_count}
