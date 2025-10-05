from django.shortcuts import render, redirect, get_object_or_404
from .models import (Product_image,Products,category,Cart_Items,shipping,Payment,HeroImage,Order,OrderItem)
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
            return redirect("addproductimage") 
    images = Product_image.objects.filter(user=request.user)
    return render(request, "upload_image.html", {"images": images})

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
        featured = bool(request.POST.get("featured"))
        category_id = request.POST.get("category")
        slug = slugify(name)
        stock = int(request.POST.get("stock"))

        # Relations
        category_obj = category.objects.get(id=category_id) if category_id else None

        image_id1 = request.POST.get("product_image")
        image_id2 = request.POST.get("product_image2")
        image_id3 = request.POST.get("product_image3")

        image_obj1 = Product_image.objects.filter(id=image_id1, user=request.user).first() if image_id1 else None
        image_obj2 = Product_image.objects.filter(id=image_id2, user=request.user).first() if image_id2 else None
        image_obj3 = Product_image.objects.filter(id=image_id3, user=request.user).first() if image_id3 else None

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
            product_image=image_obj1,
            product_image2=image_obj2,
            product_image3=image_obj3,
            slug=slug,
            stock=stock,
        )
        return redirect("product_lists")

    products = Products.objects.filter(user=request.user).order_by("-published")
    categories = category.objects.all()
    images = Product_image.objects.filter(user=request.user)

    return render(
        request,
        "user/product_list.html",
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
        return redirect("product_lists")

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

import io
import requests
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db import transaction
from django.utils.dateparse import parse_datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

from .models import Payment, Cart_Items, Order, OrderItem  # adjust import path to your app
# Note: if your models live in other apps, import accordingly

@login_required
def verify_payment(request):
    reference = request.GET.get("reference")
    if not reference:
        return render(request, "payment_failed.html", {"error": "No payment reference provided."})

    # Find payment for this user
    payment = get_object_or_404(Payment, reference=reference, user=request.user)

    # Prevent double-processing
    if getattr(payment, "verified", False):
        # Optionally fetch order related to this payment if you store it
        # return existing success page
        return render(request, "payment_success.html", {"payment": payment})

    # Verify with Paystack
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        res_data = response.json()
    except Exception as e:
        return render(request, "payment_failed.html", {"error": f"Connection error: {str(e)}"})

    # Check Paystack response
    if res_data.get("status") and res_data.get("data", {}).get("status") == "success":
        data = res_data["data"]

        # Parse paid_at (if present)
        paid_at_raw = data.get("paid_at")
        paid_at_dt = None
        if paid_at_raw:
            try:
                paid_at_dt = parse_datetime(paid_at_raw)
            except Exception:
                paid_at_dt = None

        # Convert amount (Paystack returns amount in kobo)
        try:
            amount_naira = (Decimal(data.get("amount")) / Decimal("100")) if data.get("amount") is not None else Decimal("0.00")
        except (InvalidOperation, TypeError):
            amount_naira = Decimal("0.00")

        # Start DB transaction to avoid partial writes
        with transaction.atomic():
            # Update payment record
            payment.verified = True
            payment.amount = amount_naira
            payment.channel = data.get("channel") or ""
            if paid_at_dt:
                payment.paid_at = paid_at_dt
            payment.save(update_fields=["verified", "amount", "channel", "paid_at"])

            # Fetch cart items BEFORE clearing (only un-purchased items)
            cart_items_qs = Cart_Items.objects.select_related("product", "product__user") \
                                .filter(user=request.user, purchased=False)
            cart_items = list(cart_items_qs)

            # If cart empty, still show success
            if not cart_items:
                return render(request, "payment_success.html", {"payment": payment})

            # Calculate total_amount safely (use Decimal)
            total_amount = Decimal("0.00")
            for item in cart_items:
                # Ensure unit price is Decimal
                unit_raw = getattr(item.product, "discountedprice", None) or getattr(item.product, "actualprice", None) or Decimal("0.00")
                try:
                    unit_price = Decimal(unit_raw)
                except (InvalidOperation, TypeError):
                    unit_price = Decimal("0.00")
                line_total = unit_price * (item.quantity or 0)
                total_amount += line_total

            # Create order
            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
                status="completed"  # adjust status as you prefer
            )

            # Convert cart items into order items and update stock
            for item in cart_items:
                unit_raw = getattr(item.product, "discountedprice", None) or getattr(item.product, "actualprice", None) or Decimal("0.00")
                try:
                    unit_price = Decimal(unit_raw)
                except (InvalidOperation, TypeError):
                    unit_price = Decimal("0.00")

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    seller=getattr(item.product, "user", None),
                    quantity=item.quantity,
                    price=unit_price,
                )

                # Reduce stock if applicable
                prod = item.product
                if getattr(prod, "stock", None) is not None:
                    try:
                        current = int(prod.stock or 0)
                        new_stock = max(0, current - int(item.quantity or 0))
                        if new_stock != current:
                            prod.stock = new_stock
                            prod.save(update_fields=["stock"])
                    except Exception:
                        # If stock field isn't integer-like, skip silently (or log)
                        pass

                # Mark cart item purchased so it won't be picked again
                item.purchased = True
                item.save(update_fields=["purchased"])

        # ---------- Generate PDF receipt ----------
        try:
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            # Header
            p.setFont("Helvetica-Bold", 18)
            p.drawCentredString(width / 2, height - 50, "TrustBuySell Receipt")

            # Customer info
            p.setFont("Helvetica", 12)
            p.drawString(50, height - 100, f"Customer: {request.user.get_full_name() or request.user.username}")
            p.drawString(50, height - 120, f"Email: {request.user.email or ''}")
            p.drawString(50, height - 140, f"Reference: {payment.reference}")
            p.drawString(50, height - 160, f"Payment Channel: {payment.channel}")
            p.drawString(50, height - 180, f"Date: {payment.paid_at or ''}")

            # Product table
            data_table = [["Product", "Qty", "Unit Price (₦)", "Total (₦)"]]
            for item in cart_items:
                try:
                    unit_price = Decimal(getattr(item.product, "discountedprice", None) or getattr(item.product, "actualprice", None) or "0.00")
                except Exception:
                    unit_price = Decimal("0.00")
                line_total = unit_price * (item.quantity or 0)
                data_table.append([
                    str(item.product.name),
                    str(item.quantity),
                    f"{unit_price:,.2f}",
                    f"{line_total:,.2f}",
                ])
            data_table.append(["", "", "Grand Total", f"{total_amount:,.2f}"])

            table = Table(data_table, colWidths=[200, 60, 120, 120])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            table.wrapOn(p, width, height)
            # Draw table lower on page (adjust as needed)
            table.drawOn(p, 50, height - 420)

            # Footer
            p.setFont("Helvetica-Oblique", 11)
            p.drawCentredString(width / 2, 100, "Thank you for shopping with TrustBuySell!")

            p.showPage()
            p.save()
            buffer.seek(0)

            # Email receipt (optional)
            if request.user.email:
                email = EmailMessage(
                    "TrustBuySell Receipt",
                    f"Hi {request.user.username},\n\nThank you for your purchase. Please find your receipt attached.",
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                )
                email.attach(f"receipt_{payment.reference}.pdf", buffer.getvalue(), "application/pdf")
                email.send(fail_silently=True)
        except Exception:
            # If PDF/email generation fails, we still proceed (do not break order creation).
            pass

        # Clear purchased cart items
        try:
            Cart_Items.objects.filter(user=request.user, purchased=True).delete()
        except Exception:
            # If deletion fails, leave for later cleanup and optionally log
            pass

        return render(request, "payment_success.html", {"payment": payment, "order": order})

    # Payment verification failed
    error_message = res_data.get("message", "Payment verification failed.") if isinstance(res_data, dict) else "Payment verification failed."
    return render(request, "payment_failed.html", {"payment": payment, "error": error_message})


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
   

    context = {
        "products": products,
        "total_products": total_products,
        "sold_out": sold_out,
        "pending_orders":pending_orders,
    }
    return render(request, "dashboard/seller_dashboard.html", context)

@login_required(login_url="login")
def buyer_dashboard(request):
   
    return render(request, "dashboard/buyer_dashboard.html")

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
