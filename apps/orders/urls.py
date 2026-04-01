"""
URL configuration for the orders app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OrderViewSet, ShippingAddressViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'shipping-addresses', ShippingAddressViewSet, basename='shipping-address')

urlpatterns = [
    path('', include(router.urls)),
]
