from decimal import Decimal
from django.db import models
from user.models import User
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

#global class
class category(models.Model):
    name = models.CharField(max_length=30, null = True)
    image = models.ImageField( upload_to="img/", null=True) 

   
    def __str__(self):
        return self.name
    class Meta:
        verbose_name="category"
        verbose_name_plural="Category"

#userbase
class Product_image(models.Model):
    user = models.ForeignKey(User, related_name="user_image",on_delete=models.CASCADE)
    image = models.ImageField( upload_to="img/product_images/", null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True) 
    Ishero = models.BooleanField(default=False)
    def __str__(self):
        return 'image' 
   
    class Meta:
        verbose_name="Product_image"
        verbose_name_plural="Product Images"

class HeroImage(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    image = models.ImageField(upload_to="hero_images/")
    is_active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Hero Image"
        verbose_name_plural = "Hero Images"

    def __str__(self):
        return self.title or f"Hero {self.id}"


class Products(models.Model):
    STATUS_CHOICES = (
    ('draft', 'Draft'),
    ('published', 'Published'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    category = models.ForeignKey(category, related_name="product_category",on_delete=models.CASCADE,null=True)
    name = models.CharField(max_length=50, null =True)
    description = models.TextField(null =True)
    meta_keywords = models.CharField(max_length=255, null =True, help_text="seo keywords seprated with comma")
    meta_descriptions = models.CharField(max_length=255, null =True, help_text="seo description here")
    product_image = models.ForeignKey(Product_image, on_delete=models.CASCADE,null= True,related_name="prod_image")
    published = models.DateTimeField(auto_now_add =True, null=True)
    updated = models.DateTimeField(auto_now=True,null=True)
    slug = models.SlugField(null=True, max_length=100,unique=True)
    actualprice = models.DecimalField(max_digits= 20, decimal_places=2,null=True)
    discountedprice = models.DecimalField(max_digits= 20, decimal_places=2,null=True)
    status = models.CharField(max_length=30, null =True,choices = STATUS_CHOICES,default="published")
    featured = models.BooleanField(default=False, null=True,blank=True)
    product_image2 = models.ForeignKey(Product_image, on_delete=models.CASCADE,null=True,related_name="prod_image2")
    product_image3 = models.ForeignKey(Product_image, on_delete=models.CASCADE, null=True,related_name="prod_image3")
    stock = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.name} "
    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})
    class Meta:
        verbose_name="Products"
        verbose_name_plural="Products"
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=50, unique=True)
    verified = models.BooleanField(default=False)
    channel = models.CharField(max_length=50, blank=True,null=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} ({'verified' if self.verified else 'pending'})"


class Order(models.Model):
    product = models.ManyToManyField(Products, related_name="ordered_product")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")  # buyer
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=(("pending", "Pending"), ("delivery_pending", "Delivery_Pending"), ("cancelled", "Cancelled"),("delivered", "Delivered"),("paid", "Paid")),
        default="completed",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"


class OrderItem(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("waiting_for_delivery", "Waiting _For_Delivery"),
    ]

    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("Products", on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sales")
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting_for_delivery")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.status})"

    def get_total(self):
        return (self.price or Decimal("0.00")) * self.quantity

    def mark_delivered(self):
        """Mark this item as delivered."""
        self.status = "delivered"
        self.save()


class Cart_Items(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,related_name="cartitems")
    product = models.ForeignKey("Products", on_delete=models.CASCADE, related_name="cartitemsproduct")
    quantity = models.PositiveIntegerField(default=1)
    purchased = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} by {self.user}"

    def get_total(self):
        price = self.product.discountedprice or self.product.actualprice or Decimal("0.00")
        return price * self.quantity

    
class shipping(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    # items = models.ForeignKey(Cart_Items, on_delete=models.CASCADE, related_name="cartitems")
    state = models.CharField(max_length=30)
    phone = models.CharField(max_length=15)
    full_name = models.CharField(max_length=30)
    lga = models.CharField(max_length= 30)
    address = models.CharField(max_length=150)
    landmark = models.CharField(max_length=100, blank=True,null=True)

    def __str__(self):
        return f'shipping to {self.user}| {self.state} |{self.lga}| {self.address}'
    
User = settings.AUTH_USER_MODEL


class Review(models.Model):
    product = models.ForeignKey("Products", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐"
