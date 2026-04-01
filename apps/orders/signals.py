"""
Signals for the orders app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order


@receiver(post_save, sender=Order)
def send_order_confirmation(sender, instance, created, **kwargs):
    """
    Send order confirmation email when order is created.
    """
    if created:
        # TODO: Implement email sending
        # from .tasks import send_order_confirmation_email
        # send_order_confirmation_email.delay(instance.id)
        pass
