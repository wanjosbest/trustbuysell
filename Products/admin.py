from django.contrib import admin
from .models import (category, Product_image, Products,herobackimg,Cart_Items )

admin.site.register(category)
admin.site.register(Product_image)
admin.site.register(Products)
admin.site.register(herobackimg)
admin.site.register(Cart_Items)