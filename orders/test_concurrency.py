import pytest
from django.db import transaction
from myapp.models import Product  # Use your actual model name
import threading

@pytest.mark.django_db(transaction=True)
def test_inventory_lock_prevents_overselling():
    # 1. CREATE THE SHARED PRODUCT OUTSIDE THE FUNCTION
    # This laptop belongs to everyone in the test.
    product = Product.objects.create(
        name="Limited Laptop", 
        stock=1, 
        price=50000, 
        active=True
    )
    
    def attempt_purchase():
        try:
            # Each thread will now look for this SPECIFIC laptop
            with transaction.atomic():
                p = Product.objects.select_for_update().get(id=product.id)
                if p.stock > 0:
                    p.stock -= 1
                    p.save()
        except Exception:
            pass

    # 2. RUN THE THREADS
    import threading
    threads = [threading.Thread(target=attempt_purchase) for _ in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()

    # 3. VERIFY
    product.refresh_from_db()
    assert product.stock == 0  # Even with 5 people, stock should never be negative