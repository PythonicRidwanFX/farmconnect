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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, Order, OrderItem, DeliveryDetails



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

        print("Username:", username)
        print("Email:", email)
        print("User Type:", user_type)
        print("Password1:", password1)
        print("Password2:", password2)

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return render("register.html")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        user.first_name = full_name
        user.save()

        profile = Profile.objects.create(
            user=user,
            user_type=user_type,
            phone=phone,
            location=location
        )
        messages.success(request, "Account created successfully.")

        login(request, user)

        print("Registration successful!")

        if profile.user_type == "farmer":
            return redirect("farmer_dashboard")
        else:
            return redirect("marketplace")

    return render(request, "register.html")
# =========================
# 🔐 LOGIN
# =========================

def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email").strip().lower()
        password = request.POST.get("password")

        try:
            # Find user using email
            user_obj = User.objects.get(email__iexact=email)

            # Authenticate using username
            user = authenticate(
                request,
                username=user_obj.username,
                password=password
            )

            if user is not None:
                login(request, user)

                user.profile.is_online = True
                user.profile.save()

                messages.success(request, f"Welcome back, {user.first_name}!")

                if user.profile.user_type == "farmer":
                    return redirect("farmer_dashboard")
                else:
                    return redirect("marketplace")

            else:
                messages.error(request, "Incorrect password.")

        except User.DoesNotExist:
            messages.error(request, "No account exists with this email.")

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
        unit = request.POST.get("unit")
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
            quantity=float(quantity),
            unit=unit,
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
        return redirect("marketplace")

    total = sum(item.total_price for item in cart_items)

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        state = request.POST.get("state")
        city = request.POST.get("city")
        address = request.POST.get("address")
        notes = request.POST.get("notes")

        # Create Order
        order = Order.objects.create(
            buyer=request.user,
            total_price=total,
            payment_status="Pending",
            status="Pending",
        )

        # Save Delivery Details
        DeliveryDetails.objects.create(
            order=order,
            full_name=full_name,
            phone=phone,
            address=address,
            city=city,
            state=state,
            notes=notes,
        )

        # Move Cart Items to Order Items
        for item in cart_items:

            OrderItem.objects.create(
                order=order,
                product=item.product,
                farmer=item.product.farmer,
                quantity=item.quantity,
                unit_price=item.product.price,
                subtotal=item.total_price,
            )

        # Empty Cart
        cart_items.delete()
        from django.urls import reverse

        print("Order ID:", order.id)
        print("Redirect URL:", reverse("payment_page", kwargs={"order_id": order.id}))

        return redirect("payment_page", order_id=order.id)

    return render(
        request,
        "checkout.html",
        {
            "cart": cart_items,
            "total": total,
        }
    )



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
        product.unit = request.POST.get("unit")
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
    orders = (
        Order.objects
        .filter(buyer=request.user)
        .select_related("product")
        .order_by("-created_at")
    )

    return render(request, "orders.html", {
        "orders": orders
    })

@login_required
def remove_from_cart(request, id):
    product = get_object_or_404(Product, id=id)

    Cart.objects.filter(
        user=request.user,
        product=product
    ).delete()

    return redirect("cart")


from django.contrib.auth.decorators import login_required
from .models import Order

@login_required
def farmer_orders(request):

    orders = Order.objects.filter(
        product__farmer=request.user
    ).select_related(
        "buyer",
        "product"
    ).order_by("-created_at")

    return render(
        request,
        "farmer_orders.html",
        {
            "orders": orders
        }
    )

@login_required
def update_order_status(request, id, status):

    order = get_object_or_404(
        Order,
        id=id,
        product__farmer=request.user
    )

    if status in ["Pending", "Processing", "Delivered"]:
        order.status = status
        order.save()

    return redirect("farmer_orders")

@login_required
def payment_page(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        buyer=request.user
    )

    return render(
        request,
        "payment.html",
        {
            "order": order,
        }
    )

