from django.shortcuts import render, redirect, get_object_or_404
from .models import (Product_image,Products,category,Cart_Items,shipping,Payment)
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

#user product list
@login_required
def user_product_list(request):
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
        stock = request.POST.get("stock")
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
            stock = stock,
        )
        return redirect("product_list")
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
    reference = request.GET.get("reference")
    if not reference:
        return render(request, "payment_failed.html", {"error": "No payment reference provided."})

    payment = get_object_or_404(Payment, reference=reference, user=request.user)
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        res_data = response.json()
    except Exception as e:
        return render(request, "payment_failed.html", {"error": f"Connection error: {str(e)}"})

    if res_data.get("status") and res_data["data"]["status"] == "success":
        payment.verified = True
        payment.amount = res_data["data"]["amount"] / 100  # kobo → naira
        payment.channel = res_data["data"].get("channel", "")
        payment.paid_at = res_data["data"].get("paid_at")
        payment.save()

        # ✅ Fetch purchased items before clearing cart
        cart_items = list(Cart_Items.objects.filter(user=request.user))

        # ---- Generate PDF Receipt ----
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Header
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(width / 2, height - 50, "TrustBuySell Receipt")

        # Customer Info
        p.setFont("Helvetica", 12)
        p.drawString(50, height - 100, f"Customer: {request.user.get_full_name() or request.user.username}")
        p.drawString(50, height - 120, f"Email: {request.user.email}")
        p.drawString(50, height - 140, f"Reference: {payment.reference}")
        p.drawString(50, height - 160, f"Payment Channel: {payment.channel}")
        p.drawString(50, height - 180, f"Date: {payment.paid_at}")

        # Product Table
        data = [["Product", "Qty", "Unit Price (₦)", "Total (₦)"]]
        for item in cart_items:
            data.append([
                item.product.name,
                str(item.quantity),
                f"{item.product.discountedprice:,.2f}",
                f"{item.quantity * item.product.discountedprice:,.2f}"
            ])
        data.append(["", "", "Grand Total", f"{payment.amount:,.2f}"])

        table = Table(data, colWidths=[200, 60, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2563eb")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        table.wrapOn(p, width, height)
        table.drawOn(p, 50, height - 400)

        # Footer
        p.setFont("Helvetica-Oblique", 11)
        p.drawCentredString(width / 2, 100, "Thank you for shopping with TrustBuySell!")

        p.showPage()
        p.save()
        buffer.seek(0)

        # ---- Email Receipt ----
        email = EmailMessage(
            "TrustBuySell Receipt",
            f"Hi {request.user.username},\n\nThank you for your purchase. Please find your receipt attached.",
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
        )
        email.attach(f"receipt_{payment.reference}.pdf", buffer.getvalue(), "application/pdf")
        email.send()

        #  Clear cart after receipt is sent
        Cart_Items.objects.filter(user=request.user).delete()

        return render(request, "payment_success.html", {"payment": payment})

    else:
        error_message = res_data.get("message", "Payment verification failed.")
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

    context = {
        "products": products,
        "total_products": total_products,
        "sold_out": sold_out,
    }
    return render(request, "dashboard/seller_dashboard.html", context)