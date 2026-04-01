"""
URL configuration for the payments app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PaymentMethodViewSet, PaymentViewSet, WebhookViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/payment/', WebhookViewSet.as_view({'post': 'payment'}), name='payment-webhook'),
]
