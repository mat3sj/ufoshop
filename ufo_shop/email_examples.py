"""
Examples of how to use the email utility functions.

This file contains examples of how to send emails using the utility functions
in utils.py. These examples are for demonstration purposes only and are not
meant to be run directly.
"""

from typing import Dict, Any, List

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from ufo_shop.utils import send_template_email

User = get_user_model()


def send_welcome_email(user_id: int, request=None) -> None:
    """
    Send a welcome email to a new user.
    
    Args:
        user_id: The ID of the user to send the email to
        request: The request object (optional, used for building absolute URLs)
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Build context for the email template
        context = {
            'user': user,
            'shop_url': request.build_absolute_uri(reverse('shop')) if request else '#',
            'profile_url': request.build_absolute_uri(reverse('profile')) if request else '#',
        }
        
        # Send the email
        send_template_email(
            recipient_list=[user.email],
            subject="Welcome to UFO Shop!",
            template_name="ufo_shop/email/welcome.html",
            context=context,
            plain_template_name="ufo_shop/email/welcome.txt"
        )
        
    except User.DoesNotExist:
        # Handle the case where the user doesn't exist
        print(f"User with ID {user_id} does not exist")


def send_order_confirmation_email(order_id: int, request=None) -> None:
    """
    Send an order confirmation email.
    
    Args:
        order_id: The ID of the order to send the confirmation for
        request: The request object (optional, used for building absolute URLs)
    """
    # This is a mock example since we don't have an Order model
    # In a real application, you would fetch the order from the database
    
    # Mock order data
    order = {
        'number': f'ORD-{order_id}',
        'date': timezone.now().strftime('%Y-%m-%d %H:%M'),
        'items': [
            {
                'name': 'UFO Model X',
                'price': '$99.99',
                'quantity': 1,
                'total': '$99.99'
            },
            {
                'name': 'Alien Plush Toy',
                'price': '$24.99',
                'quantity': 2,
                'total': '$49.98'
            }
        ],
        'total': '$149.97'
    }
    
    # Mock user data (in a real application, you would get this from the order)
    user = {
        'email': 'customer@example.com'
    }
    
    # Build context for the email template
    context = {
        'user': user,
        'order': order,
        'order_url': request.build_absolute_uri(reverse('profile')) if request else '#',
    }
    
    # Send the email
    send_template_email(
        recipient_list=[user['email']],
        subject=f"Order Confirmation #{order['number']}",
        template_name="ufo_shop/email/order_confirmation.html",
        context=context,
        plain_template_name="ufo_shop/email/order_confirmation.txt"
    )


# Example of how to use these functions in a view
"""
from django.views.generic import CreateView
from django.contrib.auth import login
from ufo_shop.forms import SignUpForm
from ufo_shop.email_examples import send_welcome_email

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'ufo_shop/signup.html'
    success_url = '/'
    
    def form_valid(self, form):
        # Save the user
        response = super().form_valid(form)
        user = form.save()
        
        # Log the user in
        login(self.request, user)
        
        # Send welcome email
        send_welcome_email(user.id, self.request)
        
        return response
"""