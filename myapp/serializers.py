from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        # We define exactly which fields we want to expose to the public internet
        fields = ['id', 'name', 'price', 'description', 'image', 'stock', 'slug']

        read_only_fields = ['seller']