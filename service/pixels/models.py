from django.db import models
from .validators import ContentTypeRestrictedFileField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

# Create your models here.


    

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

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET("Unknown User"))
    content = models.CharField(max_length=200)
    stars = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(5)],default=0)
    date = models.CharField(max_length=50)

class ShopItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    cert_licencse = ContentTypeRestrictedFileField(upload_to='uploads/',content_types=['text/plain'],max_upload_size=5000,blank=True,null=True)
    data = ContentTypeRestrictedFileField(upload_to='uploads/',content_types=['image/jpg','image/jpeg','image/bmp','image/tga','image/png'],max_upload_size=5000,blank=True,null=True)
    data_name = models.CharField(max_length=50)

class ShopListing(models.Model):
    item = models.OneToOneField(ShopItem, on_delete=models.CASCADE)
    reception = models.ForeignKey(Comment, on_delete=models.SET("Unknown User"),blank=True,null=True)
    buyers = models.ForeignKey(User, on_delete=models.DO_NOTHING,blank=True,null=True)
    price = models.FloatField(validators=[MinValueValidator(0.0),MaxValueValidator(1000000000)])
    description = models.CharField(max_length=300)
    sold = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(100)],default=0)
    

class ForumPost(models.Model):
    creator = models.ForeignKey(User,on_delete=models.SET("Unknown User"))
    content = models.CharField(max_length=500)
    date = models.CharField(max_length=50)

class ForumTopic(models.Model):
    creator = models.ForeignKey(User,on_delete=models.SET("Unknown User"))
    posts = models.ForeignKey(ForumPost,on_delete=models.SET("Unknown User"),blank=True,null=True)
    creation_date = models.CharField(max_length=50)
    last_post = models.CharField(max_length=50)
    num_Posts = models.IntegerField()


class Gift(models.Model):
    code = models.CharField(max_length=20)
    key = models.CharField(max_length=100)
    users = models.ForeignKey(User,on_delete=models.SET("Unknown User"))
    

    


