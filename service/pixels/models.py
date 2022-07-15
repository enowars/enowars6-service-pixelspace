from django.db import models
from .validators import ContentTypeRestrictedFileField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

# Create your models here.

class ShopItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50,db_index=True)
    cert_license = ContentTypeRestrictedFileField(upload_to='uploads/licenses/',content_types=['text/plain'],max_upload_size=1000,blank=True,null=True)
    data = ContentTypeRestrictedFileField(upload_to='uploads/image_data/',content_types=['image/jpg','image/jpeg','image/bmp','image/tga','image/png'],max_upload_size=1000,blank=True,null=True)


class ShopListing(models.Model):
    item = models.OneToOneField(ShopItem, on_delete=models.CASCADE)
    price = models.IntegerField(validators=[MinValueValidator(1),MaxValueValidator(2147483646)])
    description = models.CharField(max_length=300)
    sold = models.IntegerField(validators=[MinValueValidator(0)],default=0)

class Comment(models.Model):
    item = models.ForeignKey(ShopListing,on_delete=models.CASCADE,db_index=True,related_name="item_listing")
    user = models.ForeignKey(User,on_delete=models.CASCADE,db_index=True,related_name="creator")
    content = models.CharField(max_length=200)
    stars = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(5)],default=3)
    date = models.CharField(max_length=50)

class Buyers(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,db_index=True,related_name="buyer_user")
    item = models.ForeignKey(ShopItem,on_delete=models.CASCADE,db_index=True,related_name="buyer_item")
    data = models.CharField(max_length=100)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.IntegerField(default=100,validators=[MinValueValidator(0),MaxValueValidator(2**60)])
    notes = models.CharField(max_length=50000,default="You can enter your notes here...")
    expiration_date = models.DateTimeField(blank=True,null=True)

@receiver(post_save,sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance,balance=100,expiration_date=timezone.now() + timedelta(minutes=11))

@receiver(post_save, sender=User)
def save_user_profile(sender,instance,**kwargs):
    instance.profile.save()



class Gift(models.Model):
    code = models.CharField(max_length=50)
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE,related_name="gift_item")
    users = models.ForeignKey(Buyers, on_delete=models.CASCADE,blank=True,null=True,db_index=True,related_name="Receivers")