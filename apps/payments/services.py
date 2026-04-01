"""
Payment gateway service (Mock implementation).
"""
import uuid
from datetime import datetime

from django.utils import timezone

from .models import Payment, Transaction


class MockPaymentGateway:
    """
    Mock payment gateway for demonstration purposes.
    In production, replace with actual Stripe, PayPal, or other gateway integration.
    """
    
    @staticmethod
    def process_payment(payment, card_number=None, cvv=None, expiry=None):
        """
        Process a payment through the mock gateway.
        
        Args:
            payment: Payment model instance
            card_number: Card number (for demo: use '4242424242424242' for success)
            cvv: CVV code
            expiry: Expiry date (MM/YY)
        
        Returns:
            dict: Transaction result
        """
        # Create transaction record
        transaction = Transaction.objects.create(
            payment=payment,
            transaction_type=Transaction.Type.CHARGE,
            amount=payment.amount,
            status=Transaction.Status.PENDING
        )
        
        # Mock validation
        if not card_number or len(card_number) < 13:
            transaction.status = Transaction.Status.FAILED
            transaction.error_message = "Invalid card number"
            transaction.save()
            return {
                'success': False,
                'error': 'Invalid card number',
                'transaction_id': str(transaction.id)
            }
        
        # Mock success/failure based on card number
        # 4242424242424242 = Success
        # 4000000000000002 = Declined
        # Any other = Random result
        
        if card_number == '4242424242424242':
            success = True
        elif card_number == '4000000000000002':
            success = False
        else:
            import random
            success = random.choice([True, True, True, False])  # 75% success rate
        
        gateway_transaction_id = f"MOCK-{uuid.uuid4().hex[:16].upper()}"
        
        if success:
            transaction.status = Transaction.Status.SUCCESS
            transaction.gateway_transaction_id = gateway_transaction_id
            transaction.gateway_response = {
                'id': gateway_transaction_id,
                'status': 'succeeded',
                'amount': float(payment.amount),
                'currency': payment.currency,
                'created': int(datetime.now().timestamp())
            }
            transaction.save()
            
            # Update payment
            payment.status = Payment.Status.COMPLETED
            payment.transaction_id = gateway_transaction_id
            payment.completed_at = timezone.now()
            
            # Extract card details for display
            payment.card_last_four = card_number[-4:]
            payment.card_brand = MockPaymentGateway._get_card_brand(card_number)
            payment.save()
            
            # Update order
            from apps.orders.models import Order
            payment.order.payment_status = Order.PaymentStatus.PAID
            payment.order.status = Order.Status.CONFIRMED
            payment.order.save()
            
            return {
                'success': True,
                'transaction_id': gateway_transaction_id,
                'amount': float(payment.amount),
                'currency': payment.currency
            }
        else:
            transaction.status = Transaction.Status.FAILED
            transaction.gateway_transaction_id = gateway_transaction_id
            transaction.error_message = "Card was declined"
            transaction.gateway_response = {
                'id': gateway_transaction_id,
                'status': 'failed',
                'error': 'Card was declined'
            }
            transaction.save()
            
            payment.status = Payment.Status.FAILED
            payment.save()
            
            return {
                'success': False,
                'error': 'Card was declined',
                'transaction_id': gateway_transaction_id
            }
    
    @staticmethod
    def refund_payment(payment, amount=None):
        """
        Process a refund.
        
        Args:
            payment: Payment model instance
            amount: Amount to refund (None for full refund)
        
        Returns:
            dict: Refund result
        """
        refund_amount = amount or payment.amount
        
        transaction = Transaction.objects.create(
            payment=payment,
            transaction_type=Transaction.Type.REFUND,
            amount=refund_amount,
            status=Transaction.Status.PENDING
        )
        
        # Mock refund processing
        gateway_transaction_id = f"MOCK-REFUND-{uuid.uuid4().hex[:12].upper()}"
        
        transaction.status = Transaction.Status.SUCCESS
        transaction.gateway_transaction_id = gateway_transaction_id
        transaction.gateway_response = {
            'id': gateway_transaction_id,
            'status': 'succeeded',
            'amount': float(refund_amount),
            'refunded': True
        }
        transaction.save()
        
        # Update payment status
        if refund_amount >= payment.amount:
            payment.status = Payment.Status.REFUNDED
        payment.save()
        
        # Update order
        from apps.orders.models import Order
        payment.order.payment_status = Order.PaymentStatus.REFUNDED
        payment.order.save()
        
        return {
            'success': True,
            'transaction_id': gateway_transaction_id,
            'amount': float(refund_amount)
        }
    
    @staticmethod
    def _get_card_brand(card_number):
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


class PaymentService:
    """
    Service class for payment operations.
    """
    
    @staticmethod
    def create_payment(order, method=Payment.Method.CREDIT_CARD):
        """
        Create a new payment for an order.
        """
        payment = Payment.objects.create(
            order=order,
            user=order.user,
            amount=order.total,
            method=method
        )
        return payment
    
    @staticmethod
    def process_order_payment(order, payment_details):
        """
        Process payment for an order.
        
        Args:
            order: Order instance
            payment_details: dict with card details
        
        Returns:
            Payment result
        """
        # Create payment record
        payment = PaymentService.create_payment(order)
        
        # Process through gateway
        result = MockPaymentGateway.process_payment(
            payment,
            card_number=payment_details.get('card_number'),
            cvv=payment_details.get('cvv'),
            expiry=payment_details.get('expiry')
        )
        
        return result
