"""
Signals for the reviews app.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review, ReviewHelpfulness


@receiver(post_save, sender=Review)
def update_product_rating(sender, instance, created, **kwargs):
    """
    Update product average rating when a review is saved.
    """
    instance.product.update_rating()


@receiver(post_delete, sender=Review)
def update_product_rating_on_delete(sender, instance, **kwargs):
    """
    Update product average rating when a review is deleted.
    """
    instance.product.update_rating()


@receiver(post_save, sender=ReviewHelpfulness)
def update_helpful_counts(sender, instance, created, **kwargs):
    """
    Update review helpful counts when a vote is saved.
    """
    review = instance.review
    
    if created:
        if instance.vote == ReviewHelpfulness.Vote.HELPFUL:
            review.helpful_count += 1
        else:
            review.not_helpful_count += 1
        review.save(update_fields=['helpful_count', 'not_helpful_count'])


@receiver(post_delete, sender=ReviewHelpfulness)
def update_helpful_counts_on_delete(sender, instance, **kwargs):
    """
    Update review helpful counts when a vote is deleted.
    """
    review = instance.review
    
    if instance.vote == ReviewHelpfulness.Vote.HELPFUL:
        review.helpful_count = max(0, review.helpful_count - 1)
    else:
        review.not_helpful_count = max(0, review.not_helpful_count - 1)
    review.save(update_fields=['helpful_count', 'not_helpful_count'])
