"""
Utility functions for the users app.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_password_reset_email(user, token):
    """
    Send password reset email to user.
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    subject = 'Password Reset Request'
    html_message = render_to_string('emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(user):
    """
    Send welcome email to new users.
    """
    subject = 'Welcome to Our E-commerce Platform!'
    html_message = render_to_string('emails/welcome.html', {
        'user': user,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )
