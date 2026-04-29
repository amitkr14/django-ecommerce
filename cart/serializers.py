from rest_framework import serializers
from myapp.models import Product
from .models import CartItem

# 1. Translate the Product details
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # We only send what the frontend needs to show in the cart
        fields = ['id', 'name', 'price', 'image'] 

# 2. Translate the Cart Item
class CartItemSerializer(serializers.ModelSerializer):
    # This nests the Product data inside the CartItem data
    product = ProductSerializer(read_only=True)
    # This grabs that @property we built in your models!
    total_price = serializers.ReadOnlyField() 

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']