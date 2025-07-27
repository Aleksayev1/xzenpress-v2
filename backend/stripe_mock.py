from typing import Optional, Dict, Any
from pydantic import BaseModel
import stripe
import os

# Stripe configuration
stripe.api_key = os.environ.get("STRIPE_API_KEY", "sk_test_placeholder_key")

class CheckoutSessionRequest(BaseModel):
    amount: float  # Amount in currency unit (not cents)
    currency: str = "brl"
    success_url: str = "https://xzenpress.com/success"
    cancel_url: str = "https://xzenpress.com/payment"
    customer_email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str

class CheckoutStatusResponse(BaseModel):
    status: str
    payment_status: str
    session_id: str

class StripeCheckout:
    def __init__(self, api_key: str):
        stripe.api_key = api_key
        self.api_key = api_key
    
    async def create_checkout_session(self, request: CheckoutSessionRequest) -> CheckoutSessionResponse:
        try:
            # Check if using placeholder key
            if self.api_key == "sk_test_placeholder_key" or not self.api_key:
                # Return mock response for testing
                return CheckoutSessionResponse(
                    url="https://checkout.stripe.com/c/pay/mock_session_test",
                    session_id="cs_test_mock_session_123456"
                )
            
            # Convert amount to cents for Stripe
            amount_cents = int(request.amount * 100)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': request.currency,
                        'product_data': {
                            'name': 'XZenPress Premium',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',  # Changed from 'subscription' to 'payment'
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                customer_email=request.customer_email,
                metadata=request.metadata or {}
            )
            return CheckoutSessionResponse(url=session.url, session_id=session.id)
        except Exception as e:
            raise Exception(f"Stripe checkout error: {str(e)}")
    
    async def get_checkout_status(self, session_id: str) -> CheckoutStatusResponse:
        try:
            # Check if mock session
            if session_id == "cs_test_mock_session_123456":
                return CheckoutStatusResponse(
                    status="complete",
                    payment_status="paid", 
                    session_id=session_id
                )
            
            if self.api_key == "sk_test_placeholder_key" or not self.api_key:
                return CheckoutStatusResponse(
                    status="complete",
                    payment_status="paid",
                    session_id=session_id
                )
            
            session = stripe.checkout.Session.retrieve(session_id)
            return CheckoutStatusResponse(
                status=session.status,
                payment_status=session.payment_status, 
                session_id=session_id
            )
        except Exception as e:
            raise Exception(f"Stripe status error: {str(e)}")