from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    USER_TYPE = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE)

    phone = models.CharField(max_length=20, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)

    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.username

    def last_seen_display(self):
        if self.is_online:
            return "Online"

        if not self.last_seen:
            return "Offline"

        diff = timezone.now() - self.last_seen
        seconds = diff.total_seconds()

        if seconds < 60:
            return "Last seen just now"
        elif seconds < 3600:
            return f"Last seen {int(seconds // 60)} min ago"
        elif seconds < 86400:
            return f"Last seen {int(seconds // 3600)} hr ago"
        else:
            return f"Last seen {int(seconds // 86400)} day(s) ago"

# ======================
# 🌾 PRODUCT
# ======================
class Product(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.FloatField()
    quantity = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ======================
# 🛒 CART
# ======================
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

    @property
    def total_price(self):
        return self.product.price * self.quantity


# ======================
# 📦 ORDER
# ======================
class Order(models.Model):
    STATUS = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Delivered', 'Delivered'),
    )

    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.FloatField()
    status = models.CharField(max_length=50, choices=STATUS, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order by {self.buyer.username}"


# ======================
# 💬 CHAT ROOM
# ======================
class ChatRoom(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmer_rooms')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_rooms')

    def __str__(self):
        return f"{self.farmer.username} & {self.buyer.username}"


# ======================
# 💬 MESSAGE
# ======================
class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    message = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)

    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.message[:20] if self.message else 'file'}"

    class Meta:
        ordering = ['timestamp']