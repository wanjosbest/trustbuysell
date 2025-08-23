from django.shortcuts import render,redirect
from.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout,login
from Products.models import category,herobackimg, Products

def register_view(request):
    if request.method == 'POST':
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        seller = request.POST.get("seller")
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
            shopowner = seller,
            phone_number = phone_number,
        )
        user.set_password(password)
        user.save()
        messages.info(request, "Account created Successfully!")
        return redirect('login')
    return render(request, 'user/register.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not User.objects.filter(username=username).exists():
            messages.error(request, 'Invalid username')
            return redirect('login')
        user = authenticate(username=username, password=password)
        
        if user is None:
            messages.error(request, "Invalid Password")
            return redirect('login')
        else:
            login(request,user)
            return redirect("index")
    return render(request, 'user/login.html')

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
    FeaturedProduct = Products.objects.filter(featured = True).order_by("-published")[:8]
   
    context = {"categories":categories,"FeaturedProduct":FeaturedProduct}
    return render(request,"index.html", context)
