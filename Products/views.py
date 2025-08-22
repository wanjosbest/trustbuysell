from django.shortcuts import render, redirect, get_object_or_404
from .models import (Product_image,Products,category,Cart_Items)
from user.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify


#users to add products images

@login_required
def upload_image(request):
    if request.method == "POST":
        if "image" in request.FILES:
            image_file = request.FILES["image"]
            Product_image.objects.create(
                user=request.user,
                image=image_file
            )
            return redirect("addproductimage")  # reload same page or redirect elsewhere

    images = Product_image.objects.filter(user=request.user)
    return render(request, "upload_image.html", {"images": images})


#global displaying products

@login_required
def product_list(request):
    # Handle product creation inside the same page)
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        meta_keywords = request.POST.get("meta_keywords")
        meta_descriptions = request.POST.get("meta_descriptions")
        actualprice = request.POST.get("actualprice")
        discountedprice = request.POST.get("discountedprice")
        status = request.POST.get("status")
        featured = bool(request.POST.get("featured"))
        category_id = request.POST.get("category")
        image_id = request.POST.get("product_image")
        image_id2 = request.FILES.get("product_image2")
        image_id3 = request.FILES.get("product_image3")
        slug = slugify(name)
        # Relations
        category_obj = category.objects.get(id=category_id) if category_id else None
        image_obj = request.FILES.get("product_image")
      

        # Save product
        product = Products.objects.create(
            user=request.user,
            name=name,
            description=description,
            meta_keywords=meta_keywords,
            meta_descriptions=meta_descriptions,
            actualprice=actualprice,
            discountedprice=discountedprice,
            status=status,
            featured=featured,
            category=category_obj,
            product_image=image_obj,
            product_image2=image_id2,
            product_image3=image_id3,
            slug=slug,
        )
        return redirect("product_list")

    products = Products.objects.filter(user=request.user).order_by("-published")
    categories = category.objects.all()
    images = Product_image.objects.filter(user=request.user)

    return render(
        request,
        "product_list.html",
        {
            "products": products,
            "categories": categories,
            "images": images,
        },
    )

def product_detail(request, slug):
    product = get_object_or_404(Products, slug=slug, status="published")
    related_product = (
        Products.objects.filter(category=product.category, status="published")
        .exclude(id=product.id)
        .order_by("?")[:3]   
    )
    context = {
        "product": product,
        "related_product": related_product,
    }
    return render(request, "product_detail.html", context)

@login_required
def product_update(request, slug):
    product = get_object_or_404(Products, slug=slug)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.meta_keywords = request.POST.get("meta_keywords")
        product.meta_descriptions = request.POST.get("meta_descriptions")
        product.actualprice = request.POST.get("actualprice")
        product.discountedprice = request.POST.get("discountedprice")
        product.status = request.POST.get("status")
        product.featured = bool(request.POST.get("featured"))

        # category
        category_id = request.POST.get("category")
        product.category = category.objects.get(id=category_id) if category_id else None

        # images
        product_image_id = request.POST.get("product_image")
        product_image2_id = request.POST.get("product_image2")
        product_image3_id = request.POST.get("product_image3")

        product.product_image = Product_image.objects.get(id=product_image_id) if product_image_id else None
        product.product_image2 = Product_image.objects.get(id=product_image2_id) if product_image2_id else None
        product.product_image3 = Product_image.objects.get(id=product_image3_id) if product_image3_id else None

        product.save()
        return redirect("product_list")

    categories = category.objects.all()
    images = Product_image.objects.filter(user=request.user)

    return render(
        request,
        "product_update.html",
        {
            "product": product,
            "categories": categories,
            "images": images,
        },
    )

@login_required
def product_delete(request, slug):
    product = get_object_or_404(Products, slug=slug)
    if request.method == "POST":
        product.delete()
        return redirect("product_list")
    return render(request, "product_delete.html", {"product": product})

#add to cart
@login_required
def add_to_cart(request,product_id):
    product = get_object_or_404(Products, id= product_id)

    cart_item, created = Cart_Items.objects.get_or_create(
        user = request.user,
        product = product,
    )
    if not created:
        cart_item.quantity +=1
        cart_item.save()
    return redirect("cart")
@login_required
def view_cart(request):
    cart_items = Cart_Items.objects.filter(user = request.user)
    total = sum(item.get_total() for item in cart_items)
    context = {
        "cart_items":cart_items,
        "total":total,
    }
    
    return render(request, "cart.html", context)

@login_required
def remove_item(request, product_id):
    if request.method =="POST":
        remove_cart_item = get_object_or_404(
        Cart_Items, 
        product_id=product_id, 
        user=request.user
    )
        remove_cart_item.delete()
   
    return redirect("cart")