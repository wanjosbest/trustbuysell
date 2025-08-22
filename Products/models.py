from django.db import models
from user.models import User


class herobackimg(models.Model):
    image = models.ImageField( upload_to="img/", null=True) 

    class Meta:
        verbose_name="herobackimg"
        verbose_name_plural="Hero image"



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
    image = models.ImageField( upload_to="img/", null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True) 
    def __str__(self):
        return 'image' 
   
    class Meta:
        verbose_name="Product_image"
        verbose_name_plural="Product Images"

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
    def __str__(self):
        return f"{self.name} "
    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})
    class Meta:
        verbose_name="Products"
        verbose_name_plural="Products"