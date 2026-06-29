from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.db.models import Q
from django.utils import timezone

from .models import (
    Product,
    Cart,
    Order,
    OrderItem,
    DeliveryDetails,
    Profile,
    ChatRoom,
    Message,
)


# =========================
# 🌾 LANDING PAGE
# =========================
def landing(request):
    return render(request, "landing.html")

# =========================
# 📝 REGISTER
# =========================
# =========================
# 📝 REGISTER
# =========================
def register(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        location = request.POST.get("location", "").strip()
        user_type = request.POST.get("user_type", "").strip()
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, "register.html")

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        user.first_name = full_name
        user.save()

        # The profile was already created by signals.py
        profile = user.profile
        profile.user_type = user_type
        profile.phone = phone
        profile.location = location
        profile.is_online = True
        profile.save()

        login(request, user)

        messages.success(request, "Account created successfully.")

        if profile.user_type == "farmer":
            return redirect("farmer_dashboard")

        return redirect("marketplace")

    return render(request, "register.html")


# =========================
# 🔐 LOGIN
# =========================
def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email__iexact=email)

            user = authenticate(
                request=request,
                username=user_obj.username,
                password=password
            )

            if user is None:
                messages.error(request, "Incorrect password.")
                return render(request, "login.html")

            login(request, user)

            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={
                    "user_type": "buyer",
                    "phone": "",
                    "location": "",
                }
            )

            profile.is_online = True
            profile.save()

            messages.success(request, f"Welcome back, {user.first_name}!")

            if profile.user_type == "farmer":
                return redirect("farmer_dashboard")
            else:
                return redirect("marketplace")

        except User.DoesNotExist:
            messages.error(request, "No account exists with this email.")

    return render(request, "login.html")


# =========================
# 🚪 LOGOUT
# =========================
# =========================
# 🚪 LOGOUT
# =========================
def user_logout(request):
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()

        if profile:
            profile.is_online = False
            profile.last_seen = timezone.now()
            profile.save()

    logout(request)
    return redirect("landing")


@login_required
def farmer_dashboard(request):
    # Safely get the user's profile
    profile = Profile.objects.filter(user=request.user).first()

    if profile is None:
        return render(request, "error.html", {
            "message": "No profile found for this user."
        })

    if profile.user_type != "farmer":
        return redirect("marketplace")

    products = Product.objects.filter(farmer=request.user)

    total_value = sum(product.price for product in products)
    total_products = products.count()

    context = {
        "products": products,
        "total_value": total_value,
        "total_products": total_products,
        "profile": profile,
    }

    return render(request, "farmer_dashboard.html", context)

@login_required
def add_product(request):
    # only farmers allowed
    if not hasattr(request.user, "profile") or request.user.profile.user_type != "farmer":
        messages.error(request, "Only farmers can add products.")
        return redirect("marketplace")

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        price = request.POST.get("price", "").strip()
        quantity = request.POST.get("quantity", "").strip()
        unit = request.POST.get("unit", "").strip()
        description = request.POST.get("description", "").strip()
        image = request.FILES.get("image")

        # ✅ VALIDATION (IMPORTANT FIX)
        if not name or not price or not quantity or not unit or not description:
            messages.error(request, "All fields are required.")
            return redirect("add_product")

        try:
            price = float(price)
            quantity = float(quantity)
        except ValueError:
            messages.error(request, "Price and quantity must be valid numbers.")
            return redirect("add_product")

        # prevent duplicate product
        if Product.objects.filter(farmer=request.user, name=name).exists():
            messages.warning(request, "You already added this product.")
            return redirect("farmer_dashboard")

        # save product
        Product.objects.create(
            farmer=request.user,
            name=name,
            description=description,
            price=price,
            quantity=quantity,
            unit=unit,
            image=image
        )

        messages.success(request, "Product added successfully.")
        return redirect("farmer_dashboard")

    return render(request, "add_product.html")


# =========================
# 🛒 MARKETPLACE
# =========================
def marketplace(request):
    query = (request.GET.get("q") or "").strip()
    min_price = request.GET.get("min")
    max_price = request.GET.get("max")

    products = Product.objects.all().order_by("-created_at")

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

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


# =========================
# 📦 PRODUCTS
# =========================
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


# =========================
# 🛒 VIEW CART
# =========================
@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)

    total = sum(item.total_price for item in cart_items)

    return render(request, "cart.html", {
        "cart": cart_items,
        "total": total
    })


# =========================
# ➕ ADD TO CART
# =========================
@login_required
def add_to_cart(request, id):
    product = get_object_or_404(Product, id=id)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Product added to cart.")
    return redirect("cart")
# =========================
# 🛒 CHECKOUT
# =========================
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

        # Create Order Items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                farmer=item.product.farmer,
                quantity=item.quantity,
                unit_price=item.product.price,
                subtotal=item.total_price,
            )

        # Clear Cart
        cart_items.delete()

        return redirect("payment_page", order_id=order.id)

    return render(request, "checkout.html", {
        "cart": cart_items,
        "total": total,
    })


# =========================
# 💬 START CHAT
# =========================
@login_required
def start_chat(request, farmer_id):
    farmer = get_object_or_404(User, id=farmer_id)

    if request.user == farmer:
        return redirect("marketplace")

    room, created = ChatRoom.objects.get_or_create(
        farmer=farmer,
        buyer=request.user
    )

    return redirect("chat_room", room.id)


# =========================
# 💬 CHAT ROOM
# =========================
@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)

    messages = Message.objects.filter(room=room).order_by("timestamp")

    return render(request, "chat.html", {
        "room": room,
        "messages": messages
    })


# =========================
# 📦 PRODUCT DETAIL
# =========================
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)

    return render(request, "product_detail.html", {
        "product": product
    })


# =========================
# ✏️ EDIT PRODUCT
# =========================
@login_required
def edit_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.user != product.farmer:
        return redirect("farmer_dashboard")

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.quantity = request.POST.get("quantity")
        product.unit = request.POST.get("unit")

        if request.FILES.get("image"):
            product.image = request.FILES.get("image")

        product.save()

        messages.success(request, "Product updated successfully.")
        return redirect("farmer_dashboard")

    return render(request, "edit_product.html", {
        "product": product
    })


# =========================
# 🗑 DELETE PRODUCT
# =========================
def delete_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.user == product.farmer:
        product.delete()
        messages.success(request, "Product deleted successfully.")

    return redirect("farmer_dashboard")

@login_required
def orders(request):
    orders = (
        Order.objects
        .filter(buyer=request.user)
        .prefetch_related("items__product")
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

    messages.success(request, "Item removed from cart.")
    return redirect("cart")


@login_required
def farmer_orders(request):

    orders = (
        Order.objects
        .filter(items__farmer=request.user)
        .distinct()
        .prefetch_related("items__product", "items__farmer")
        .select_related("buyer")
        .order_by("-created_at")
    )

    return render(request, "farmer_orders.html", {
        "orders": orders
    })


# =========================
# 🔄 UPDATE ORDER STATUS
# =========================
@login_required
def update_order_status(request, id, status):

    order = get_object_or_404(
        Order,
        id=id,
        items__farmer=request.user
    )

    if status in ["Pending", "Processing", "Delivered", "Completed", "Cancelled"]:
        order.status = status
        order.save()
        messages.success(request, "Order status updated successfully.")

    return redirect("farmer_orders")


# =========================
# 💳 PAYMENT PAGE
# =========================
@login_required
def payment_page(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        buyer=request.user
    )

    return render(request, "payment.html", {
        "order": order
    })