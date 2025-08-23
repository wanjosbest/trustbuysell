from django.contrib import admin
from .models import (category, Product_image, Products,Cart_Items,shipping,Payment,HeroImage,Order,OrderItem)

admin.site.register(category)
admin.site.register(Product_image)
admin.site.register(Products)

admin.site.register(Cart_Items)
admin.site.register(shipping)
admin.site.register(Payment)
admin.site.register(HeroImage)
admin.site.register(Order)
admin.site.register(OrderItem)