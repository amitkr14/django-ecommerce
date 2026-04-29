from django.shortcuts import render,redirect
from .forms import AddressForm
from .models import Address,Order,OrderItem
from cart.cart import Cart
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order
from cart.cart import Cart 
import razorpay
from django.conf import settings



client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))



def add_address(request):
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address=None    
    if request.method=="POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            return redirect("index")
    form = AddressForm(instance=address)
    return render(request,'orders/add_address.html',{'form':form})

    

def place_order(request):
    order_success=False
    if request.method=="POST":
        cart = Cart(request)
        total_amount= cart.get_total_price()

        if request.user.is_authenticated:
            order = Order.objects.create(user=request.user,total_amount=total_amount)
            for item in cart:
                OrderItem.objects.create(order=order,product=item['product'],quantity=item['qty'])
            order_success=True    
        else:
            order = Order.objects.create(total_amount=total_amount)
            for item in cart:
                OrderItem.objects.create(order=order,product=item['product'],quantity=item['qty'])
            order_success=True    
    return JsonResponse({'success':order_success})


def order_success(request):
    return render(request,'orders/order-success.html')

def order_failed(request):
    return redirect(request,'orders/order-failed.html')

def checkout(request):
    # If you need to pass cart totals or items to the template, you would do it here!
    return render(request, 'orders/checkout.html')




def checkout(request):
    cart = Cart(request)
    cart_total = cart.get_total_price()
    
    return render(request, 'orders/checkout.html', {'cart_total': cart_total})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_razorpay_order(request):
    # 1. Securely fetch the actual cart total from the backend database!
    cart = Cart(request)
    cart_total = cart.get_total_price()
    
    # Optional safety check: Don't let them pay for an empty cart
    if cart_total <= 0:
        return Response({'error': 'Your cart is empty!'}, status=400)
    
    # 2. Razorpay strictly accepts amounts in PAISE. 
    # Convert Decimal to integer paise (e.g., ₹40997.00 * 100 = 4099700)
    amount_in_paise = int(cart_total * 100) 
    
    # 3. Tell Razorpay to create an order with the REAL amount
    payment_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"receipt_{request.user.id}"
    }
    razorpay_order = client.order.create(data=payment_data)
    
    # 4. Save the order in your database with the REAL amount
    order = Order.objects.create(
        user=request.user,
        amount=cart_total, # Save the actual Rupee amount in your DB
        razorpay_order_id=razorpay_order['id']
    )
    
    return Response({
        'status': 'success',
        'razorpay_order_id': razorpay_order['id'],
        'amount': amount_in_paise,
        'currency': 'INR'
    })