from django.db import models
from .validators import ContentTypeRestrictedFileField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.postgres.fields import HStoreField

# Create your models here.
class Comment(models.Model):
    content = models.CharField(max_length=200)
    stars = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(5)],default=3)
    date = models.CharField(max_length=50)

class MultiUserDict(models.Model):
    name = models.CharField(max_length=70)

    def __str__(self):
        return self.name

class Buyers(models.Model):
    container = models.ForeignKey(MultiUserDict,on_delete=models.CASCADE, db_index=True)
    key = models.CharField(max_length=100, db_index=True)
    value = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return str(self.container)

class Receptions(models.Model):
    container = models.ForeignKey(MultiUserDict,on_delete=models.CASCADE, db_index=True,related_name="Container")
    key = models.CharField(max_length=100, db_index=True)
    value = models.ForeignKey(Comment,on_delete=models.CASCADE, db_index=True,related_name="Reception")

    def __str__(self):
        return str(self.container)
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    balance = models.FloatField(validators=[MinValueValidator(0.0)])
    cryptographic_key = models.CharField(max_length=1000,default="None")
    notes = models.CharField(max_length=50000,default="You can enter your notes here...")

@receiver(post_save,sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance,balance=1.0)

@receiver(post_save, sender=User)
def save_user_profile(sender,instance,**kwargs):
    instance.profile.save()

class ShopItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    cert_licencse = ContentTypeRestrictedFileField(upload_to='uploads/',content_types=['text/plain'],max_upload_size=5000,blank=True,null=True)
    data = ContentTypeRestrictedFileField(upload_to='uploads/',content_types=['image/jpg','image/jpeg','image/bmp','image/tga','image/png'],max_upload_size=5000,blank=True,null=True)
    data_name = models.CharField(max_length=50)

class ShopListing(models.Model):
    item = models.OneToOneField(ShopItem, on_delete=models.CASCADE)
    reception = models.ForeignKey(MultiUserDict, on_delete=models.CASCADE,blank=True,null=True,name="Receptions",related_name="Comment")
    buyers = models.ForeignKey(MultiUserDict, on_delete=models.CASCADE,blank=True,null=True,name="Buyers",related_name="User")
    price = models.FloatField(validators=[MinValueValidator(0.0),MaxValueValidator(100000000001.0)])
    description = models.CharField(max_length=300)
    sold = models.IntegerField(validators=[MinValueValidator(0)],default=0)

class Gift(models.Model):
    code = models.CharField(max_length=20)
    value = models.CharField(max_length=100)
    users = models.ForeignKey(MultiUserDict, on_delete=models.CASCADE,blank=True,null=True,name="Receivers",related_name="Receivers")