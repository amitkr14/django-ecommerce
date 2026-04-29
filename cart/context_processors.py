from .models import Cart

def cart(request):
    # Only try to count the cart if the user is logged in
    if request.user.is_authenticated:
        # Try to find their cart in the database
        cart_obj = Cart.objects.filter(user=request.user).first()
        
        if cart_obj:
            # Sum up the quantities of all items in their cart
            total_qty = sum(item.quantity for item in cart_obj.items.all())
            return {'cart_count': total_qty}
            
    # If not logged in, or cart is empty, return 0
    return {'cart_count': 0}