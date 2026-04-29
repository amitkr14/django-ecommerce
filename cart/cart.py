from  myapp.models import Product
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Cart as CartModel, CartItem


class Cart:
    def __init__(self, request):
        self.request = request
        self.user = request.user
        
        # Ensure the user is logged in to use the persistent cart
        if self.user.is_authenticated:
            # get_or_create safely fetches their existing cart, or makes a new one
            self.cart_obj, _ = CartModel.objects.get_or_create(user=self.user)
        else:
            self.cart_obj = None

    def add(self, product, product_qty):
        if not self.cart_obj:
            raise Exception("User must be logged in to add to cart.")
            
        # STOCK VALIDATION: Check before doing anything
        if product_qty > product.stock:
            raise ValueError(f"Sorry, only {product.stock} items available in stock.")

        # See if the item is already in their cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=self.cart_obj, 
            product=product,
            defaults={'quantity': product_qty}
        )

        # If it was already there, add to the quantity
        if not created:
            new_qty = cart_item.quantity + product_qty
            
            # STOCK VALIDATION: Check the combined amount
            if new_qty > product.stock:
                raise ValueError(f"You cannot add more. Only {product.stock} in stock.")
            
            cart_item.quantity = new_qty
            cart_item.save()

    def update(self, product, qty):
        if not self.cart_obj: return
        
        # STOCK VALIDATION: Check the new requested amount
        if qty > product.stock:
            raise ValueError(f"Only {product.stock} available.")
            
        try:
            cart_item = CartItem.objects.get(cart=self.cart_obj, product=product)
            if qty > 0:
                cart_item.quantity = qty
                cart_item.save()
            else:
                self.delete(product) # If they set qty to 0, remove it
        except CartItem.DoesNotExist:
            pass

    def delete(self, product):
        if not self.cart_obj: return
        CartItem.objects.filter(cart=self.cart_obj, product=product).delete()

    def get_total_price(self):
        if not self.cart_obj: return 0
        # Sum up all the real-time calculated prices
        return sum(item.total_price for item in self.cart_obj.items.all())

    # We use this to easily loop over items in the HTML template
    def get_items(self):
        if not self.cart_obj: return []
        return self.cart_obj.items.all()


# class Cart():
#     def __init__(self, request):
#         self.session = request.session
#         cart = request.session.get('cart')
#         if 'cart' not in request.session:
#             cart = self.session['cart']={}
#         self.cart=cart
#     def __len__(self):
#         return sum (int(item['qty']) for item in self.cart.values() if item.get('qty'))
    
#     def get_total_price(self):
#         return sum(Decimal(item['price'])* Decimal(item['qty']) for item in self.cart.values())
    
#     def __iter__(self):
#         product_ids = self.cart.keys()
#         products = Product.objects.filter(id__in=product_ids)
#         cart= self.cart.copy()

#         for product in products:
#             cart[str(product.id)]['product']=product


#         for item in cart.values():
#             item['price']=Decimal(item['price'])
#             item['qty']=Decimal(item['qty'])
#             item['total']=item['price']*item['qty']
#             yield item    





#     def add(self, product, product_qty):
#         product_id = str(product.id)
#         if product_id in self.cart:
#             self.cart[product_id]['qty']+=product_qty
#         else:
#             self.cart[product_id]={'price':str(product.price),'qty':product_qty}
#         self.session.modified=True                

#     def delete(self, product_id):
#         product_id = str(product_id)
#         if product_id in self.cart:
#             del self.cart[product_id]
#         self.session.modified=True

#     def update(self,product, qty):
#         product_id= str(product.id)
#         product_quantity = qty
#         if product_id in self.cart:
#             self.cart[product_id]['qty']=product_quantity
#         self.session.modified=True                    
