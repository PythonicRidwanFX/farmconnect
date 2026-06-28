from django.db.models.signals import post_save
from django.contrib.auth.models import User
<<<<<<< HEAD
from django.dispatch import receiver
from .models import Profile

=======
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


>>>>>>> df4708b9815261166538935075d15908a8cc5dfc
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
<<<<<<< HEAD
            user_type="buyer"   # default value
        )


=======
            user_type="buyer"  # default role (important)
        )
>>>>>>> df4708b9815261166538935075d15908a8cc5dfc
@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()