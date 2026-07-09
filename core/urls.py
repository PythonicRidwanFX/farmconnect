from django.urls import path
from . import views

urlpatterns = [
    # 🌾 Landing & Authentication
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # 🛒 Products
    path('products/', views.products, name='products'),
    path('add-product/', views.add_product, name='add_product'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('product/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('product/delete/<int:id>/', views.delete_product, name='delete_product'),

    # 🌾 Farmer Dashboard
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer/orders/', views.farmer_orders, name='farmer_orders'),

    # 🛒 Marketplace
    path('marketplace/', views.marketplace, name='marketplace'),

    # 🛒 Cart
    path('cart/', views.view_cart, name='cart'),
    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:id>/', views.remove_from_cart, name='remove_from_cart'),

    # 📦 Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders, name='orders'),
    path('order/update/<int:id>/<str:status>/', views.update_order_status, name='update_order_status'),

    # 💳 Payment
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),

    # 💬 Chat
    path('chat/start/<int:farmer_id>/', views.start_chat, name='start_chat'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path("payment/verify/",views.verify_payment,name="verify_payment"),
]