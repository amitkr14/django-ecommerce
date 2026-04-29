
from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('<slug:slug>',views.detail,name='detail'),
    path('sell/', views.add_product, name='add_product'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/products/<int:pk>/', views.api_product_detail, name='api_product_detail'),
    path('api/seller/dashboard/', views.api_seller_dashboard, name='api_seller_dashboard'),
    path('api/seller/product/add/', views.api_seller_add_product, name='api_seller_add_product'),
    path('api/seller/product/<int:product_id>/update/', views.api_seller_update_product, name='api_seller_update_product'),
    path('seller/register',views.seller_register,name='seller_register'),
    path('seller/login',views.seller_login,name='seller_login'),
    path('seller/dashboard',views.seller_dashboard,name='seller_dashboard'),
    path('seller/product/<int:product_id>/edit/', views.seller_edit_product, name='seller_edit_product'),

    path('api/payment/create/', views.create_razorpay_order, name='create_razorpay_order'),
    path('api/payment/verify/', views.verify_payment, name='verify_payment'),
]