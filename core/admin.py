from django.contrib import admin
from .models import Product, Order, Profile, Cart

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Profile)
admin.site.register(Cart)