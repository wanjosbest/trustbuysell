from django.shortcuts import render,redirect
from.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout,login
from Products.models import category, Products,Product_image,HeroImage

def register_view(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        user_type = request.POST.get("user_type")

        user = User.objects.filter(username=username)
        if user.exists():
            messages.info(request, "Username already taken!")
            return redirect('register')
        if confirm_password != password:
            messages.error(request,"Password Mismatched")
            return redirect("register")
        user = User.objects.create_user(
            first_name=firstname,
            last_name=lastname,
            username=username,
            email = email,
            phone_number = phone_number,
        )
        user.set_password(password)
        if user_type == "seller":
           user.is_seller = True
        elif user_type == "buyer":
            user.is_buyer = True
        else:
            messages.info(request, "You Must select Buyer or Seller")
            return redirect("register")
        user.save()
        messages.info(request, "Account created Successfully!")
        return redirect('login')
    return render(request, 'user/register.html')

def login_view(request):
    next_url = request.GET.get("next","")
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get("next")
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'Invalid username')
            return redirect('login')
        user = authenticate(username=username, password=password)
        
        if user is None:
            messages.error(request, "Invalid Password")
            return redirect('login')
        else:
            login(request,user)
            if next_url:
                return redirect(next_url)
            elif user.is_seller == True:
               return redirect("seller_dashboard")
            else:
                return redirect("buyer_dashboard")
    return render(request, 'user/login.html',{"next_url":next_url})



# logout user
@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')

# homepage 
def index(request):
    #Output categories
    categories = category.objects.all()
    #output featured products
    hero = HeroImage.objects.filter(is_active=True).first()
    FeaturedProduct = Products.objects.filter(featured = True).order_by("-published")[:8]
   
    context = {"categories":categories,"FeaturedProduct":FeaturedProduct,"hero":hero}
    return render(request,"index.html", context)

# def header(request):
#     categories = category.objects.all()
#     context = {"categories":categories }
#     return render(request,"footer.html", context)