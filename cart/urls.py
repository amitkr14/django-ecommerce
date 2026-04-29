from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart-overview',views.cart_overview,name='cart-overview'),
    path('delete/<int:product_id>/', views.cart_delete, name='cart_delete'),
    path('update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('update-ajax/', views.cart_update_ajax, name='cart_update_ajax'),
    path('api/overview/', views.api_cart_overview, name='api_cart_overview'),
    path('api/add/<int:product_id>/', views.api_cart_add, name='api_cart_add'),
    path('api/update/<int:product_id>/', views.api_cart_update, name='api_cart_update'),
    path('api/delete/<int:product_id>/', views.api_cart_delete, name='api_cart_delete'),

]