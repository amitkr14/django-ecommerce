from django.shortcuts import render, redirect
from django.http import JsonResponse
from .cart import Cart
from myapp.models import Product
from django.shortcuts import get_object_or_404
import json
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import CartItemSerializer
from drf_spectacular.utils import extend_schema


# Create your views here.
@login_required(login_url='login') 
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    
    if request.method == 'POST':
        product_qty = int(request.POST.get('quantity', 1))

        try:
            cart.add(product=product, product_qty=product_qty)
            messages.success(request, f"{product.name} was added to your cart!")
            
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('detail', slug=product.slug) 

@login_required(login_url='login')
def cart_overview(request):
    cart = Cart(request)
    
    
    context = {
        'cart_items': cart.get_items(),
        'cart_total': cart.get_total_price()
    }
    return render(request, 'cart/cart-overview.html', context)

@login_required(login_url='login')
def cart_delete(request, product_id):
    if request.method == 'POST':
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        cart.delete(product=product)
        messages.success(request, f"{product.name} was removed from your cart.")
        
    return redirect('cart-overview')


@login_required(login_url='login')
def cart_update(request, product_id):
    if request.method == 'POST':
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        new_qty = int(request.POST.get('quantity'))
        
        try:
            cart.update(product=product, qty=new_qty)
            # Add this success message!
            messages.success(request, f"{product.name} quantity updated to {new_qty}.")
        except ValueError as e:
            messages.error(request, str(e))
            
    return redirect('cart-overview')
  
    
@require_POST
@login_required 
def cart_update_ajax(request):
    if request.method == 'POST':
        cart = Cart(request)
        data = json.loads(request.body)
        
        product_id = data.get('product_id')
        new_qty = int(data.get('qty'))
        if new_qty <= 0:

            return JsonResponse({

                'status': 'error',
                'message': 'Invalid quantity'
            }, status=400)

    
        product = get_object_or_404(Product, id=product_id)
        
        try:
            # Try to update the cart
            cart.update(product=product, qty=new_qty)
            item_total = product.price*new_qty
            return JsonResponse({
                'status': 'success',
                'message': 'Cart updated successfully!',
                'cart_total': float(cart.get_total_price()),
                'item_total': float(item_total),   
                'product_id': product.id     
            })
            
        except ValueError as e:
            # If the service threw a stock error, catch it and tell the user!
            return JsonResponse({
                'status': 'error',
                'message': str(e) # e.g., "Only 10 available."
            }, status=400)    
    

@api_view(['GET']) 
@permission_classes([IsAuthenticated]) 
def api_cart_overview(request):
    cart = Cart(request)
    items = cart.get_items()
    
    serializer = CartItemSerializer(items, many=True)
    
    return Response({
        'status': 'success',
        'cart_total': cart.get_total_price(),
        'items': serializer.data
    })

@extend_schema(
    summary="Add an item to the cart",
    description="Requires a valid Product ID in the URL and a JSON body with the desired quantity.",
    request={"application/json": {"type": "object", "properties": {"quantity": {"type": "integer", "example": 2}}}},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    
    quantity = int(request.data.get('quantity', 1))
    
    try:
        cart.add(product=product, product_qty=quantity)
        return Response({
            'status': 'success',
            'message': f'{product.name} added to cart.'
        })
    except ValueError as e:
        return Response({
            'status': 'error', 
            'message': str(e)
        }, status=400)
    

@api_view(['POST'])    
@permission_classes([IsAuthenticated])
def api_cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    new_qty = int(request.data.get('quantity',1))

    try:
        cart.update(product=product, quantity=new_qty)

        return Response({
            'status': 'success',
            'message': f'{product.name} successfully updated to {new_qty} quantity',
            'cart_total': cart.get_total_price(),
        })
    except ValueError as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=400)
    
@api_view(['DELETE', 'POST']) 
@permission_classes([IsAuthenticated])
def api_cart_delete(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    cart.delete(product=product)
    
    return Response({
        'status': 'success',
        'message': f'{product.name} removed from cart.',
        'cart_total': cart.get_total_price()
    })    