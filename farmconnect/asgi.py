import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
<<<<<<< HEAD
from farmconnect.core.routing import websocket_urlpatterns
=======
from core.routing import websocket_urlpatterns
>>>>>>> df4708b9815261166538935075d15908a8cc5dfc

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmconnect.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})