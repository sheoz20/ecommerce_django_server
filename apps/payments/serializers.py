"""
Serializers for the payments app.
"""
from rest_framework import serializers

from apps.orders.models import Order

from .models import Payment, PaymentMethod, Transaction


class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer for payment methods.
    """
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'method_type', 'card_last_four', 'card_brand',
            'card_expiry_month', 'card_expiry_year', 'is_default',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class CreatePaymentMethodSerializer(serializers.Serializer):
    """
    Serializer for creating payment methods.
    """
    method_type = serializers.ChoiceField(choices=PaymentMethod.Type.choices)
    card_number = serializers.CharField(max_length=19, required=False)
    card_expiry_month = serializers.CharField(max_length=2, required=False)
    card_expiry_year = serializers.CharField(max_length=4, required=False)
    cvv = serializers.CharField(max_length=4, required=False)
    is_default = serializers.BooleanField(default=False)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for transactions.
    """
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'amount', 'status',
            'gateway_transaction_id', 'error_message', 'created_at'
        ]
        read_only_fields = ['created_at']


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for payments.
    """
    transactions = TransactionSerializer(many=True, read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order_number', 'amount', 'currency', 'method',
            'status', 'transaction_id', 'card_last_four', 'card_brand',
            'transactions', 'created_at', 'completed_at'
        ]
        read_only_fields = ['created_at', 'completed_at']


class ProcessPaymentSerializer(serializers.Serializer):
    """
    Serializer for processing payments.
    """
    order_id = serializers.UUIDField(required=True)
    payment_method = serializers.ChoiceField(
        choices=Payment.Method.choices,
        default=Payment.Method.CREDIT_CARD
    )
    card_number = serializers.CharField(max_length=19, required=False)
    card_expiry = serializers.CharField(max_length=5, required=False)
    cvv = serializers.CharField(max_length=4, required=False)
    save_card = serializers.BooleanField(default=False)

    def validate_order_id(self, value):
        """Validate order exists and belongs to user."""
        user = self.context['request'].user
        try:
            order = Order.objects.get(id=value, user=user)
            if order.payment_status == Order.PaymentStatus.PAID:
                raise serializers.ValidationError("Order is already paid.")
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")


class RefundSerializer(serializers.Serializer):
    """
    Serializer for processing refunds.
    """
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0.01
    )
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        payment = self.context.get('payment')
        if not payment:
            raise serializers.ValidationError("Payment not found.")
        
        refund_amount = data.get('amount') or payment.amount
        
        if refund_amount > payment.amount:
            raise serializers.ValidationError(
                "Refund amount cannot exceed payment amount."
            )
        
        if payment.status != Payment.Status.COMPLETED:
            raise serializers.ValidationError(
                "Can only refund completed payments."
            )
        
        return data
