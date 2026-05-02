from celery import shared_task
import time
from .recommendations import update_product_similarities

@shared_task
def send_payment_receipt(email_address, order_id):
    print(f"CELERY WORKER: Starting to generate PDF receipt for Order {order_id}...")
    
    # Simulate a slow 5-second process (connecting to Gmail, generating PDF)
    time.sleep(5) 
    
    print(f"CELERY WORKER: Successfully sent receipt to {email_address}!")
    return "Email Sent"

@shared_task
def compute_similar_products_task():
    """Runs the machine learning script in the background."""
    update_product_similarities()
    return "Similarities calculated and cached."