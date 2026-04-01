"""
Views for the payments app.
"""
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.orders.models import Order

from .models import Payment, PaymentMethod, Transaction
from .serializers import (
    CreatePaymentMethodSerializer,
    PaymentMethodSerializer,
    PaymentSerializer,
    ProcessPaymentSerializer,
    RefundSerializer,
)
from .services import PaymentService


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for payment operations.
    """
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

    @action(detail=False, methods=['post'])
    def process(self, request):
        """
        Process payment for an order.
        """
        serializer = ProcessPaymentSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        order = serializer.validated_data['order_id']
        payment_details = {
            'card_number': serializer.validated_data.get('card_number'),
            'cvv': serializer.validated_data.get('cvv'),
            'expiry': serializer.validated_data.get('card_expiry')
        }

        # Process payment
        result = PaymentService.process_order_payment(order, payment_details)

        if result['success']:
            payment = Payment.objects.get(order=order)
            return Response({
                'success': True,
                'message': 'Payment processed successfully.',
                'payment': PaymentSerializer(payment).data
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Payment failed')
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Process refund for a payment.
        """
        payment = self.get_object()
        
        serializer = RefundSerializer(
            data=request.data,
            context={'payment': payment}
        )
        serializer.is_valid(raise_exception=True)

        from .services import MockPaymentGateway
        
        result = MockPaymentGateway.refund_payment(
            payment,
            amount=serializer.validated_data.get('amount')
        )

        if result['success']:
            return Response({
                'success': True,
                'message': 'Refund processed successfully.',
                'refund_amount': result['amount']
            })
        else:
            return Response({
                'success': False,
                'error': 'Refund failed'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_payments(self, request):
        """
        Get current user's payments.
        """
        payments = Payment.objects.filter(user=request.user)
        page = self.paginate_queryset(payments)
        
        if page is not None:
            serializer = PaymentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payment method operations.
    """
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(
            user=self.request.user,
            is_active=True
        )

    def create(self, request):
        """
        Create a new payment method.
        """
        serializer = CreatePaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        
        # In a real implementation, you would tokenize the card with a payment gateway
        # For this mock, we'll just store masked details
        card_number = data.get('card_number', '')
        
        payment_method = PaymentMethod.objects.create(
            user=request.user,
            method_type=data['method_type'],
            card_last_four=card_number[-4:] if card_number else '',
            card_brand=self._get_card_brand(card_number),
            card_expiry_month=data.get('card_expiry_month', ''),
            card_expiry_year=data.get('card_expiry_year', ''),
            is_default=data.get('is_default', False),
            token=f"mock_token_{request.user.id}_{PaymentMethod.objects.count()}"
        )

        return Response(
            PaymentMethodSerializer(payment_method).data,
            status=status.HTTP_201_CREATED
        )

    def _get_card_brand(self, card_number):
        """Determine card brand from number."""
        if card_number.startswith('4'):
            return 'Visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return 'Mastercard'
        elif card_number.startswith(('34', '37')):
            return 'American Express'
        elif card_number.startswith('6'):
            return 'Discover'
        return 'Unknown'

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set payment method as default.
        """
        payment_method = self.get_object()
        payment_method.is_default = True
        payment_method.save()
        
        return Response({
            'message': 'Payment method set as default.'
        })

    def destroy(self, request, pk=None):
        """
        Soft delete payment method.
        """
        payment_method = self.get_object()
        payment_method.is_active = False
        payment_method.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class WebhookViewSet(viewsets.ViewSet):
    """
    ViewSet for handling payment gateway webhooks.
    """
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def payment(self, request):
        """
        Handle payment webhook from gateway.
        """
        # In a real implementation, verify webhook signature
        # and process the event
        
        event_type = request.data.get('type')
        transaction_id = request.data.get('transaction_id')
        
        # Process webhook event
        if event_type == 'payment.success':
            # Update payment status
            pass
        elif event_type == 'payment.failed':
            # Handle failed payment
            pass
        elif event_type == 'refund.completed':
            # Handle refund
            pass
        
        return Response({'status': 'received'})
