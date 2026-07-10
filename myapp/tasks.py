from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from orders.models import Order

@shared_task
def send_payment_receipt(user_email, order_id):
    
    #Asynchronously sends a payment confirmation email via Amazon SES.
    
    try:
        # 1. Fetch the order details
        order = Order.objects.get(id=order_id)
        
        # 2. Construct the email content
        subject = f"Payment Successful - Order #{order.razorpay_order_id}"
        
        # Plain text version (fallback)
        text_message = f"Thank you for your purchase! Your payment of ₹{order.total_amount} was successful."
        
        # HTML version (The professional standard)
        html_message = f"""
        <html>
            <body>
                <h2>Order Confirmation</h2>
                <p>Thank you for shopping with IndiaShop.</p>
                <p><strong>Order ID:</strong> {order.razorpay_order_id}</p>
                <p><strong>Amount Paid:</strong> ₹{order.total_amount}</p>
                <p>We are processing your order and will notify you when it ships!</p>
            </body>
        </html>
        """
        
        # 3. Fire the email through AWS SES
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
            html_message=html_message  # Django automatically handles the multi-part email!
        )
        
        return f"Successfully sent receipt to {user_email}"

    except Order.DoesNotExist:
        return f"Failed: Order {order_id} not found."
    except Exception as e:
        return f"Failed to send email: {str(e)}"