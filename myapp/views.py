from django.shortcuts import render,redirect
from .models import Product
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProductForm
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from .serializers import ProductSerializer
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from functools import wraps
import razorpay
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from orders.models import Order
from cart.cart import Cart
from django.db import transaction
from django.core.cache import cache
from .tasks import send_payment_receipt

def customer_only(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        # If they are logged in AND are a seller, force them back to the dashboard
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('seller_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper_func


def seller_only(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        # If they are logged in but NOT a seller, kick them to the home page
        if request.user.is_authenticated and not request.user.is_staff:
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper_func

@customer_only
def index(request):
    # 1. Figure out what the user is looking for
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    # 2. CREATE A DYNAMIC CACHE KEY
    # Example: If they search "mouse" on page 1, the key is 'products_search:mouse_page:1'
    cache_key = f'products_search:{search_query}_page:{page_number}'

    # 3. Ask Redis if it has this EXACT search and page saved
    context = cache.get(cache_key)

    # 4. THE CACHE MISS
    if not context:
        print(f"CACHE MISS: Hitting Database for {cache_key}")
        
        # --- YOUR ORIGINAL SEARCH & PAGINATION LOGIC ---
        products_list = Product.objects.filter(active=True).order_by('id')
        
        if search_query:
            products_list = products_list.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
            
        paginator = Paginator(products_list, 3)
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
        }
        # -----------------------------------------------

        # Save the fully built context dictionary into Redis for 15 minutes
        cache.set(cache_key, context, timeout=900)
    
    # 5. THE CACHE HIT
    else:
        print(f"CACHE HIT: Served {cache_key} instantly from RAM!")

    return render(request, 'myapp/index.html', context)
   
@customer_only
def detail(request,slug):
    product = Product.objects.get(slug=slug)
    return render(request,'myapp/detail.html',{'product':product})


@login_required(login_url='login') 
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            new_product = form.save(commit=False)
            new_product.active = True 
            new_product.save()
            messages.success(request, f"'{new_product.name}' was successfully added to IndiaShop!")
            return redirect('index') 
    else:
        form = ProductForm()
        
    return render(request, 'myapp/add_product.html', {'form': form})

@api_view(['GET', 'POST'])
def api_products(request):
    if request.method == 'GET':
        products = Product.objects.filter(active=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(active=True) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=ProductSerializer, operation_description="Upload a new product to the IndiaShop catalog.")
@api_view(['GET', 'POST'])
def api_products(request):
    if request.method == 'GET':
        products = Product.objects.filter(active=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
        
    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(active=True) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def api_product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProductSerializer(product)
        return Response(serializer.data)
        
    elif request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == 'DELETE':
        product.delete()
        return Response({'message': 'Product deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_seller_dashboard(request):
    # SENIOR DEV MOVE: Filter strictly by request.user
    # This guarantees a seller ONLY sees their own products
    products = Product.objects.filter(seller=request.user)
    serializer = ProductSerializer(products, many=True)
    
    return Response({
        'status': 'success',
        'my_products': serializer.data
    })

# 2. ADD A NEW PRODUCT
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_seller_add_product(request):
    serializer = ProductSerializer(data=request.data)
    
    if serializer.is_valid():
        # Save the product, but force the 'seller' to be the person logged in!
        serializer.save(seller=request.user)
        return Response({
            'status': 'success',
            'message': 'Product added successfully!',
            'product': serializer.data
        })
        
    return Response(serializer.errors, status=400)

# 3. UPDATE AN EXISTING PRODUCT
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_seller_update_product(request, product_id):
    try:
        # Fetch the product, but ONLY if this user owns it!
        product = Product.objects.get(id=product_id, seller=request.user)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found or you do not have permission to edit it.'}, status=403)
    serializer = ProductSerializer(product, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'status': 'success',
            'message': 'Product updated successfully!',
            'product': serializer.data
        })
        
    return Response(serializer.errors, status=400)
@seller_only
def seller_register(request):
    if request.method== 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.save()
            return redirect('seller_dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'myapp/seller_register.html', {'form': form})

def seller_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            return redirect('seller_dashboard')
    else:
        form = AuthenticationForm()
        
    return render(request, 'myapp/seller_login.html', {'form': form})

@login_required(login_url='seller_login')
@seller_only
def seller_dashboard(request):
    my_products = Product.objects.filter(seller=request.user)
    
    context = {
        'products': my_products,
        'username': request.user.username
    }
    return render(request, 'myapp/seller_dashboard.html', context)



@login_required(login_url='seller_login')
@seller_only
def seller_edit_product(request, product_id):
    # SECURITY: We explicitly filter by 'seller=request.user'. 
    # If Seller B tries to edit Seller A's product by guessing the ID, Django blocks it.
    product = get_object_or_404(Product, id=product_id, seller=request.user)

    if request.method == 'POST':
        # instance=product tells Django to OVERWRITE the existing product, not create a new one
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{product.name}' updated successfully!")
            return redirect('seller_dashboard')
    else:
        # Pre-fill the form with the product's current data
        form = ProductForm(instance=product)

    return render(request, 'myapp/seller_edit_product.html', {'form': form, 'product': product})



# Initialize the Razorpay Client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_razorpay_order(request):
    cart = Cart(request)
    cart_total = cart.get_total_price()
    amount_in_paise = int(cart_total * 100)
    
    # 2. Tell Razorpay to create an order
    payment_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"receipt_{request.user.id}"
    }
    razorpay_order = client.order.create(data=payment_data)
    
    # 3. Save the order in your database as "Unpaid"
    order = Order.objects.create(
        user=request.user,
        total_amount= cart_total,
        razorpay_order_id=razorpay_order['id']
    )
    
    # 4. Send the ID back to the frontend to open the payment box
    return Response({
        'status': 'success',
        'razorpay_order_id': razorpay_order['id'],
        'amount': amount_in_paise,
        'currency': 'INR'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    razorpay_order_id = request.data.get('razorpay_order_id')
    razorpay_payment_id = request.data.get('razorpay_payment_id')
    razorpay_signature = request.data.get('razorpay_signature')

    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }

    try:
        # 1. Ask Razorpay if the signature is legit
        client.utility.verify_payment_signature(params_dict)
        
        # 2. START THE ATOMIC TRANSACTION HERE
        # We only update the database AFTER the bank says "Yes, they paid."
        with transaction.atomic():
            
            # Find the order they just paid for 
            # (We use select_for_update() here to lock the Order row just to be safe!)
            order = Order.objects.select_for_update().get(razorpay_order_id=razorpay_order_id)
            
            # Update the order to Paid
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.is_paid = True
            order.save()
            
            # Empty the user's cart now that they have successfully paid
            cart = Cart(request)
            cart.clear()

            send_payment_receipt.delay(request.user.email, order.id)

        # If everything inside the 'with' block succeeds, Django saves it all safely. 
        return Response({'status': 'Payment Successful!'})

    except razorpay.errors.SignatureVerificationError:
        return Response({'status': 'Payment Verification Failed!'}, status=400)

def product_list(request):
    # 1. Ask Redis: "Do you have the 'all_products' list in your memory?"
    products = cache.get('all_products')

    # 2. THE CACHE MISS (Redis is empty)
    if not products:
        print("CACHE MISS: Hitting the slow PostgreSQL Database...")
        
        # Do the heavy lifting of searching the database
        products = Product.objects.all()
        
        # Save the result into Redis for the next 15 minutes (900 seconds)
        cache.set('all_products', products, timeout=900)
    
    # 3. THE CACHE HIT
    else:
        print("CACHE HIT: Served instantly from Redis RAM!")

    return render(request, 'myapp/index.html', {'products': products}) 