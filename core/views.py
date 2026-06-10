from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from .models import Product, Cart, Order, Profile, ChatRoom, Message
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.contrib.auth import logout



# =========================
# 🌾 LANDING PAGE
# =========================
def landing(request):
    return render(request, "landing.html")


# =========================
# 📝 REGISTER
# =========================
def register(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        location = request.POST.get('location')
        user_type = request.POST.get('user_type')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            return redirect('register')

        if User.objects.filter(username=username).exists():
            return redirect('register')

        # ✅ CREATE USER
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        user.first_name = full_name
        user.save()

        # ✅ GET PROFILE FROM SIGNAL (important safety check)
        profile = user.profile
        profile.user_type = user_type
        profile.phone = phone
        profile.location = location
        profile.save()

        # 🔐 LOGIN USER
        login(request, user)

        # 🔥 FORCE ROLE REDIRECT
        if profile.user_type == "farmer":
            return redirect("farmer_dashboard")
        elif profile.user_type == "buyer":
            return redirect("marketplace")
        else:
            return redirect("login")

    return render(request, "register.html")
# =========================
# 🔐 LOGIN
# =========================


def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            # 🔥 set online
            user.profile.is_online = True
            user.profile.save()

            # 🔥 ROLE REDIRECT
            if user.profile.user_type == "farmer":
                return redirect("farmer_dashboard")
            else:
                return redirect("marketplace")

        else:
            messages.error(request, "Invalid username or password")
            return redirect("login")

    return render(request, "login.html")

# =========================
# 🚪 LOGOUT
# =========================

def user_logout(request):
    if request.user.is_authenticated:
        profile = request.user.profile
        profile.is_online = False
        profile.last_seen = timezone.now()
        profile.save()

    logout(request)
    return redirect("landing")

# =========================
# 🌾 FARMER DASHBOARD
# =========================
@login_required
def farmer_dashboard(request):
    if request.user.profile.user_type != "farmer":
        return redirect("marketplace")

    products = Product.objects.filter(farmer=request.user)

    # 💰 TOTAL VALUE (price only, NO quantity)
    total_value = sum(p.price for p in products)

    # 📦 TOTAL PRODUCTS
    total_products = products.count()

    return render(request, "farmer_dashboard.html", {
        "products": products,
        "total_value": total_value,
        "total_products": total_products
    })


# =========================
# ➕ ADD PRODUCT
# =========================
@login_required
def add_product(request):
    if request.user.profile.user_type != "farmer":
        return redirect("marketplace")

    if request.method == "POST":

        name = request.POST.get("name")
        price = request.POST.get("price")
        quantity = request.POST.get("quantity")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        # 🚨 PREVENT DUPLICATE (same farmer + same name)
        if Product.objects.filter(farmer=request.user, name=name).exists():
            return redirect("farmer_dashboard")

        Product.objects.create(
            farmer=request.user,
            name=name,
            description=description,
            price=float(price),
            quantity=int(quantity),
            image=image
        )

        return redirect("farmer_dashboard")

    return render(request, "add_product.html")
# =========================
# 🛒 MARKETPLACE (SEARCH + FILTER)
# =========================
def marketplace(request):
    query = (request.GET.get("q") or "").strip()
    min_price = request.GET.get("min")
    max_price = request.GET.get("max")

    products = Product.objects.all().order_by("-created_at")

    # 🔍 SEARCH
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    # 💰 PRICE FILTER (SAFE)
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    # 👤 SAFE USER ROLE HANDLING
    user_type = None

    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if profile:
            user_type = profile.user_type

    return render(request, "marketplace.html", {
        "products": products,
        "user_type": user_type,
        "query": query
    })

def products(request):
    query = request.GET.get("q")
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, "products.html", {
        "products": products
    })


def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)

    total = sum(item.total_price for item in cart_items)

    return render(request, "cart.html", {
        "cart": cart_items,
        "total": total
    })


def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    # check if item already exists in cart
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart')


@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('marketplace')

    for item in cart_items:
        Order.objects.create(
            buyer=request.user,
            product=item.product,
            quantity=item.quantity,
            total_price=item.product.price * item.quantity,
            status="Pending"
        )

    # clear cart after checkout
    cart_items.delete()

    return render(request, "success.html")



@login_required
def start_chat(request, farmer_id):
    farmer = get_object_or_404(User, id=farmer_id)

    # prevent self-chat
    if request.user == farmer:
        return redirect('marketplace')

    # create or get chat room
    room, created = ChatRoom.objects.get_or_create(
        farmer=farmer,
        buyer=request.user
    )

    return redirect('chat_room', room.id)

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)

    messages = Message.objects.filter(room=room).order_by('timestamp')

    return render(request, "chat.html", {
        "room": room,
        "messages": messages
    })

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    return render(request, "product_detail.html", {
        "product": product
    })
@login_required
def edit_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.user != product.farmer:
        return redirect('farmer_dashboard')

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.quantity = request.POST.get("quantity")

        if request.FILES.get("image"):
            product.image = request.FILES.get("image")

        product.save()
        return redirect('farmer_dashboard')

    return render(request, "edit_product.html", {
        "product": product
    })


@login_required
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.user == product.farmer:
        product.delete()

    return redirect('farmer_dashboard')

@login_required
def orders(request):
    return render(request, "orders.html")