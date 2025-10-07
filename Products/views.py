from django.shortcuts import render, redirect, get_object_or_404
from .models import (ProductImage,Products,category,Cart_Items,shipping,Payment,HeroImage,Order,OrderItem,Review
)
from django.core.paginator import Paginator
from user.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from .utils import generate_reference
from django.conf import settings
import requests,uuid
from django.urls import reverse
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from django.core.mail import EmailMessage
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F
from decimal import Decimal
from django.db import transaction
from django.utils.dateparse import parse_datetime
from wallet.models import Wallet, Transaction,PendingWallet

#users to add products images
@login_required
def upload_image(request):
    products = Products.objects.filter(user=request.user)

    if request.method == "POST":
        product_id = request.POST.get("product")
        image_files = request.FILES.getlist("image")  # Support multiple uploads

        if not product_id:
            messages.error(request, "Please select a product.")
            return redirect("addproductimage")

        product = get_object_or_404(Products, id=product_id, user=request.user)

        for image_file in image_files:
            ProductImage.objects.create(
                user=request.user,
                product=product,
                image=image_file
            )

        messages.success(request, "✅ Image(s) uploaded successfully.")
        return redirect("addproductimage")

    images = ProductImage.objects.filter(user=request.user)
    return render(request, "upload_image.html", {"images": images, "products": products})


#user product list
@login_required
def user_product_list(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        meta_keywords = request.POST.get("meta_keywords")
        meta_descriptions = request.POST.get("meta_descriptions")
        actualprice = request.POST.get("actualprice")
        discountedprice = request.POST.get("discountedprice")
        status = request.POST.get("status")
        category_id = request.POST.get("category")
        stock = int(request.POST.get("stock") or 0)
        slug = slugify(name)

        # Get category object
        category_obj = category.objects.filter(id=category_id).first() if category_id else None

        # Handle product image (single upload)
        product_image_file = request.FILES.get("product_image")

        image_obj = None
        if product_image_file:
            image_obj = ProductImage.objects.create(
                user=request.user,
                image=product_image_file
            )

        # Create product
        Products.objects.create(
            user=request.user,
            name=name,
            description=description,
            meta_keywords=meta_keywords,
            meta_descriptions=meta_descriptions,
            actualprice=actualprice,
            discountedprice=discountedprice,
            status=status,
            category=category_obj,
            product_image=image_obj,
            slug=slug,
            stock=stock,
        )

        return redirect("product_lists")

    # Fetch data for template
    products = Products.objects.filter(user=request.user).order_by("-published")
    categories = category.objects.all()

    return render(
        request,
        "user/product_list.html",
        {
            "products": products,
            "categories": categories,
        },
    )

# add products

@login_required
def add_product(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        meta_keywords = request.POST.get("meta_keywords")
        meta_descriptions = request.POST.get("meta_descriptions")
        actualprice = request.POST.get("actualprice")
        discountedprice = request.POST.get("discountedprice")
        status = request.POST.get("status")
        category_id = request.POST.get("category")
        stock = request.POST.get("stock")

        # Validations
        if not name or not actualprice:
            messages.error(request, "Product name and price are required.")
            return redirect("add_product")

        category_obj = category.objects.filter(id=category_id).first()

        # Unique slug generation
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Products.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Create product
        product = Products.objects.create(
            user=request.user,
            name=name,
            description=description,
            meta_keywords=meta_keywords,
            meta_descriptions=meta_descriptions,
            actualprice=actualprice,
            discountedprice=discountedprice,
            status=status,
            category=category_obj,
            slug=slug,
            stock=stock or 0,
        )

        # Handle multiple image uploads
        images = request.FILES.getlist("images")
        for img in images:
            ProductImage.objects.create(product=product, image=img)

        messages.success(request, f"✅ {product.name} added successfully!")
        return redirect("product_lists")

    categories = category.objects.all()
    return render(request, "user/add_product.html", {"categories": categories})

def product_detail(request, slug):
    product = get_object_or_404(Products, slug=slug, status="published")
    related_product = (
        Products.objects.filter(category=product.category, status="published")
        .exclude(id=product.id)
        .order_by("?")[:3]
    )
    reviews = Review.objects.filter(product=product).order_by("-created_at")

    # Fetch all product images
    images = ProductImage.objects.filter(product=product)

    if request.method == "POST":
        message = request.POST.get("message")
        rating = int(request.POST.get("rating", 0))
        if 1 <= rating <= 5:
            Review.objects.create(
                user=request.user, product=product, message=message, rating=rating
            )
            messages.success(request, "Your review has been submitted.")
            return redirect("product_detail", slug=slug)
        else:
            messages.error(request, "Please choose a rating between 1 and 5.")

    context = {
        "product": product,
        "images": images,
        "related_product": related_product,
        "reviews": reviews,
    }
    return render(request, "product_detail.html", context)


@login_required
def product_update(request, slug):
    product = get_object_or_404(Products, slug=slug, user=request.user)
    categories = category.objects.all()

    if request.method == "POST":
        # Basic product info
        product.name = request.POST.get("name", "").strip()
        product.description = request.POST.get("description", "").strip()
        product.meta_keywords = request.POST.get("meta_keywords", "").strip()
        product.meta_descriptions = request.POST.get("meta_descriptions", "").strip()
        product.actualprice = request.POST.get("actualprice") or 0
        product.discountedprice = request.POST.get("discountedprice") or 0
        product.stock = request.POST.get("stock") or 0
        product.status = request.POST.get("status", "draft")

        # Update slug when name changes
        new_slug = slugify(product.name)
        if new_slug != product.slug:
            product.slug = new_slug

        # Update category
        category_id = request.POST.get("category")
        if category_id:
            try:
                product.category = category.objects.get(id=category_id)
            except category.DoesNotExist:
                messages.warning(request, "⚠️ Invalid category selected.")

        product.save()

        # Handle new image uploads
        new_images = request.FILES.getlist("product_images")
        if new_images:
            for img in new_images:
                ProductImage.objects.create(
                    user=request.user,
                    product=product,
                    image=img
                )

        messages.success(request, "✅ Product updated successfully!")
        return redirect("product_lists")

    context = {
        "product": product,
        "categories": categories,
    }
    return render(request, "product_update.html", context)

@login_required
def product_delete(request, slug):
    product = get_object_or_404(Products, slug=slug)
    if request.method == "POST":
        product.delete()
        return redirect("product_lists")
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


@login_required(login_url="login")
def view_cart(request):
    cart_items = Cart_Items.objects.filter(user=request.user)
    subtotal = sum(item.get_total() for item in cart_items)
    return render(request, "cart.html", {"cart_items": cart_items, "subtotal": subtotal})


@login_required
def shipping_view(request):
    cartitems = Cart_Items.objects.filter(user=request.user)
    cart_total = sum(item.product.discountedprice * item.quantity for item in cartitems)
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        state = request.POST.get("state")
        lga = request.POST.get("lga")
        phone = request.POST.get("phone")
        address = request.POST.get("street")
        landmark = request.POST.get("landmark")
        savedata = shipping.objects.create(
            user=request.user,
            full_name=full_name,
            state=state,
            lga=lga,
            address=address,
            landmark=landmark,
            phone=phone,
        )
        # store shipping id for payment initialization
        request.session["shipping_id"] = savedata.id
        return redirect("initiate_payment")
    return render(request, "shippingaddress.html", {"cartitems": cartitems, "cart_total": cart_total})


@login_required
def initiate_payment(request):
    cartitems = Cart_Items.objects.filter(user=request.user)
    total_amount = sum(item.product.discountedprice * item.quantity for item in cartitems)

    if total_amount <= 0:
        return render(request, "payment_failed.html", {"error": "Cart is empty."})

    # Generate unique reference
    reference = str(uuid.uuid4()).replace("-", "")[:12]

    # Save payment object before redirecting
    payment = Payment.objects.create(
        user=request.user,
        amount=total_amount,
        reference=reference,
        verified=False
    )

    # Callback URL
    callback_url = request.build_absolute_uri(reverse("verify_payment"))

    # Paystack request
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    data = {
        "email": request.user.email,
        "amount": int(total_amount * 100),  # Paystack expects kobo
        "reference": reference,
        "callback_url": callback_url,
    }

    response = requests.post(url, headers=headers, json=data, timeout=10)
    res_data = response.json()

    if res_data.get("status"):
        auth_url = res_data["data"]["authorization_url"]
        return redirect(auth_url)
    else:
        return render(request, "payment_failed.html", {"error": res_data.get("message", "Payment init failed.")})



@login_required
def verify_payment(request):
    reference = request.GET.get("reference") or request.GET.get("trxref")

    if not reference:
        return render(request, "payment_failed.html", {"error": "Missing payment reference."})

    payment = get_object_or_404(Payment, reference=reference)

    # ✅ Avoid double-verification
    if payment.verified:
        return render(request, "payment_success.html", {"payment": payment})

    # Verify with Paystack
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
    except Exception as e:
        return render(request, "payment_failed.html", {"error": f"Network error: {e}"})

    if not result.get("status") or result["data"].get("status") != "success":
        return render(request, "payment_failed.html", {"error": "Payment not successful."})

    data = result["data"]
    amount = Decimal(data["amount"]) / 100
    paid_at = parse_datetime(data.get("paid_at", ""))

    with transaction.atomic():
        # ✅ Update payment record
        payment.verified = True
        payment.amount = amount
        payment.channel = data.get("channel", "")
        payment.paid_at = paid_at
        payment.save()

        # ✅ Get cart items
        cart_items = Cart_Items.objects.filter(user=payment.user, purchased=False)
        if not cart_items.exists():
            return render(request, "payment_success.html", {"payment": payment})

        # ✅ Create Order
        order = Order.objects.create(
            user=payment.user,
            total_amount=amount,
            status="paid",
        )

        # ✅ Create OrderItem for each cart item
        for item in cart_items:
            price = getattr(item.product, "discountedprice", item.product.actualprice)
            order_item = OrderItem.objects.create(
                order=order,
                product=item.product,
                seller=item.product.user,
                quantity=item.quantity,
                price=price,
            )

            # Add product to M2M field in Order
            order.product.add(item.product)
            # Credit seller pending wallet
            seller_pending_wallet, _ = PendingWallet.objects.get_or_create(user=item.product.user)
            seller_pending_wallet.credit(
                amount=price * item.quantity,
                description=f"Pending payment for Order #{order.id} - {item.product.name}"
            )

            # Update stock if applicable
            if hasattr(item.product, "stock"):
                item.product.stock = max(0, item.product.stock - item.quantity)
                item.product.save(update_fields=["stock"])

        # ✅ Delete all cart items after creating order
        cart_items.delete()

    return render(request, "payment_success.html", {"payment": payment, "order": order})
# buyer must confirm delivery
@login_required
def confirm_item_delivery(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    if item.status == "delivered":
        messages.info(request, "This item is already confirmed as delivered.")
        return redirect("buyer_dashboard")

    # Update item status
    item.status = "delivered"
    item.save()

    # Handle wallet transfers
    pending_wallet, _ = PendingWallet.objects.get_or_create(user=item.seller)
    seller_wallet, _ = Wallet.objects.get_or_create(user=item.seller)

    amount = item.get_total()
    if pending_wallet.balance >= amount:
        pending_wallet.debit(amount, description=f"Released for {item.product.name}")
        seller_wallet.credit(amount, description=f"Earnings from {item.product.name}")

    # If all items in the order are delivered, update the order itself
    order = item.order
    if not order.items.filter(status="pending").exists():
        order.status = "delivered"
        order.save()

    messages.success(request, f"Delivery confirmed for {item.product.name}. Seller paid successfully.")
    return redirect("buyer_dashboard")
    
                                                                                  
def search_view(request):
    query = request.GET.get("q", "")
    products = Products.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ).distinct() if query else Products.objects.none()
    categories = category.objects.filter(
        Q(name__icontains=query)  
    ).distinct() if query else category.objects.none()

    return render(request, "search_result.html", {
        "query": query,
        "products": products,
        "categories": categories,
    })
@login_required
def update_cart_quantity(request, product_id):
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            cart_item = Cart_Items.objects.get(user=request.user, product_id=product_id)
            if action == "increase":
                cart_item.quantity += 1
            elif action == "decrease" and cart_item.quantity > 1:
                cart_item.quantity -= 1
            cart_item.save()

            # calculate totals
            cart_items = Cart_Items.objects.filter(user=request.user)
            subtotal = sum(item.get_total for item in cart_items)

            return JsonResponse({
                "status": "success",
                "quantity": cart_items.quantity,
                "item_total": cart_items.get_total,
                "subtotal": subtotal
            })
        except Cart_Items.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Item not found"})
    return JsonResponse({"status": "error", "message": "Invalid request"})
@login_required(login_url="login")
def increase_quantity(request, item_id):
    item = get_object_or_404(Cart_Items, id=item_id, user=request.user)
    item.quantity += 1
    item.save()
    return redirect("cart")  # refresh cart page

@login_required(login_url="login")
def decrease_quantity(request, item_id):
    item = get_object_or_404(Cart_Items, id=item_id, user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()  
    return redirect("cart")

@login_required(login_url="login")
def remove_item(request, product_id):
    item = get_object_or_404(Cart_Items, product_id=product_id, user=request.user)
    item.delete()
    return redirect("cart")

#global product list 
def product_list(request):
    products = Products.objects.all()
    paginator = Paginator(products, 8)  # show 8 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "product_list.html", {"page_obj": page_obj})

def category_products(request, category_id):
    Category = get_object_or_404(category, id=category_id)
    products = Products.objects.filter(category=Category)

    return render(request, "products/category_products.html", {
        "category": Category,
        "products": products
    })

@login_required(login_url="login")
def seller_dashboard(request):
    products = Products.objects.filter(user=request.user)
    total_products = products.count()
    sold_out = products.filter(stock=0).count()
    pending_orders = Order.objects.all().filter(status = "pending").count()
    order = request.user.sales
    recent_order = order.all().order_by("-created_at")[:3]
    order_count = order.count()
    wallet = request.user.wallet
    Transactions = Transaction.objects.filter(wallet = wallet)
    pending_wallet = request.user.pending_wallet
    context = {
        "products": products,
        "total_products": total_products,
        "sold_out": sold_out,
        "pending_orders":pending_orders,
        "order_count":order_count,
        "recent_order": recent_order,
        "wallet":wallet,
        "Transactions":Transactions,
        "pending_wallet":pending_wallet,
    }
    return render(request, "dashboard/seller_dashboard.html", context)


@login_required(login_url="login")
def buyer_dashboard(request):
    total_items_ordered = (request.user.orders.prefetch_related("product").order_by("-created_at"))[:5]

    context ={"orders":total_items_ordered}
    # # Debug: print products for each order
    # for order in total_items_ordered:
    #     print(f"Order {order.id}: {[p.name for p in order.product.all()]}")
   
    return render(request, "dashboard/buyer_dashboard.html", context)

@login_required
def hero_image_update(request):
    hero = HeroImage.objects.filter(is_active=True).first()

    if request.method == "POST":
        title = request.POST.get("title")
        subtitle = request.POST.get("subtitle")
        image = request.FILES.get("image")

        if hero:  
            # update existing
            hero.title = title
            hero.subtitle = subtitle
            if image:
                hero.image = image
            hero.save()
        else:
            # create new
            hero = HeroImage.objects.create(
                title=title,
                subtitle=subtitle,
                image=image,
                uploaded_by=request.user,
                is_active=True
            )
        return redirect("index")  # reload page

    return render(request, "user/hero_image_form.html", {"hero": hero})

@login_required
def seller_analytics(request):
    # All items sold by this seller
    items = (
        OrderItem.objects
        .filter(seller=request.user, order__status="completed")
        .select_related("product", "order")
        .order_by("-order__created_at")
    )

    # KPIs
    totals = items.aggregate(
        total_revenue=Sum(F("price") * F("quantity")),
        total_units=Sum("quantity"),
        total_orders=Count("order", distinct=True),
    )
    total_revenue = totals["total_revenue"] or 0
    total_units = totals["total_units"] or 0
    total_orders = totals["total_orders"] or 0

    # Top products by revenue
    top_products = (
        items.values("product__id", "product__name")
        .annotate(
            revenue=Sum(F("price") * F("quantity")),
            units=Sum("quantity"),
        )
        .order_by("-revenue")[:10]
    )

    context = {
        "items": items[:50],  # recent 50 sales lines
        "total_revenue": total_revenue,
        "total_units": total_units,
        "total_orders": total_orders,
        "top_products": top_products,
    }
    return render(request, "analytics/seller_analytics.html", context)

# lists of all ordered items
@login_required(login_url='login')
def ordered_items_view(request):
    """
    Display all ordered items for the logged-in buyer.
    """
    # Fetch all items belonging to the logged-in buyer (via order relation)
    ordered_items = OrderItem.objects.filter(order__user=request.user).select_related('product', 'seller', 'order')

    #order by latest orders
    ordered_items = ordered_items.order_by('-created_at')

    context = {
        "ordered_items": ordered_items
    }
    return render(request, "products/ordered_items.html", context)



def top_rated_products(request):
    # Annotate products with their count of 5-star reviews
    top_rated = (
        Products.objects.annotate(
            five_star_count=Count('reviews', filter=Q(reviews__rating=5))
        )
        .filter(five_star_count__gt=0)
        .order_by('-five_star_count')
    )

    # Apply pagination
    paginator = Paginator(top_rated, 8)  # Show 8 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "products/top_rated_products.html", {"page_obj": page_obj})
