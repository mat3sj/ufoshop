from typing import Dict, Any, Sequence, Optional

from django.conf import settings
from django.core.mail import send_mail

from django.template.loader import render_to_string
from django.utils.html import strip_tags


def render_email_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render an email template with the given context.

    Args:
        template_name: The name of the template to render
        context: The context to use for rendering

    Returns:
        The rendered template as a string
    """
    return render_to_string(template_name, context)


def ufoshop_send_email(
    recipient_list: Sequence[str],
    subject: str,
    html_message: str,
    plain_message: Optional[str] = None
):
    """
    Send an email with both HTML and plain text versions.

    Args:
        recipient_list: List of email addresses to send to
        subject: Email subject
        html_message: HTML content of the email
        plain_message: Plain text content of the email (if None, will be generated from HTML)
    """
    # If no plain text message is provided, strip HTML tags from the HTML message
    if plain_message is None:
        plain_message = strip_tags(html_message)

    # If DEBUG is True, print email to a console instead of sending
    if settings.DEBUG:
        print("\n---------------------- EMAIL DEBUG ----------------------")
        print(f"To: {', '.join(recipient_list)}")
        print(f"From: {settings.DEFAULT_FROM_EMAIL}")
        print(f"Subject: {subject}")
        print("\n--- Plain Text Content ---")
        print(plain_message)
        print("\n--- HTML Content ---")
        print(html_message)
        print("---------------------- END EMAIL ----------------------\n")
    else:
        # Only send email if not in DEBUG mode
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
            html_message=html_message
        )


def send_template_email(
    recipient_list: Sequence[str],
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    plain_template_name: Optional[str] = None
):
    """
    Send an email using a template.

    Args:
        recipient_list: List of email addresses to send to
        subject: Email subject
        template_name: Name of the HTML template to use
        context: Context to render the template with
        plain_template_name: Name of the plain text template (if None, will strip HTML from HTML template)
    """
    # Render the HTML template
    html_message = render_email_template(template_name, context)

    # Render the plain text template if provided, otherwise strip HTML tags
    plain_message = None
    if plain_template_name:
        plain_message = render_email_template(plain_template_name, context)

    # Send the email
    ufoshop_send_email(recipient_list, subject, html_message, plain_message)


def send_order_confirmation_email(order, request=None):
    """Send order confirmation email with optional inline QR code, reusable from views and admin.

    Args:
        order: Order instance
        request: Optional HttpRequest to build absolute URLs
    """
    from django.urls import reverse
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    from email.mime.image import MIMEImage
    from django.conf import settings

    # Items and URL
    items = order.orderitem_set.all().select_related('item')
    try:
        order_url = request.build_absolute_uri(
            reverse('order_confirmation', kwargs={'pk': order.id})
        ) if request else reverse('order_confirmation', kwargs={'pk': order.id})
    except Exception:
        order_url = reverse('order_confirmation', kwargs={'pk': order.id})

    # BANK_ACCOUNT imported from models to avoid circular import of views
    from ufo_shop.models import BANK_ACCOUNT

    context = {
        'order': order,
        'items': items,
        'user': order.user,
        'order_url': order_url,
        'BANK_ACCOUNT': BANK_ACCOUNT,
    }

    # Plain part
    plain_message = render_to_string('ufo_shop/email/order_confirmation.txt', context)

    # QR handling
    qr_cid = None
    qr_bytes = b''
    if order.payment_method == 'qr_code':
        try:
            qr_bytes = order.get_payment_qr_png_bytes()
            if qr_bytes:
                qr_cid = f"qr-{order.id}@ufo-shop"
        except Exception:
            qr_bytes = b''
            qr_cid = None

    context_with_qr = {**context, 'qr_cid': qr_cid} if qr_cid else context
    html_message = render_to_string('ufo_shop/email/order_confirmation.html', context_with_qr)

    # Build and send
    msg = EmailMultiAlternatives(
        subject='Potvrzení objednávky',
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.contact_email],
    )
    msg.attach_alternative(html_message, 'text/html')

    if qr_cid and qr_bytes:
        image = MIMEImage(qr_bytes, _subtype='png')
        image.add_header('Content-ID', f'<{qr_cid}>')
        image.add_header('Content-Disposition', 'inline', filename=f'order_{order.id}_qr.png')
        msg.attach(image)

    msg.send(fail_silently=False)
