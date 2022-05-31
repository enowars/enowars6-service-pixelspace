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

@receiver(post_save,sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance,balance=1.0)

@receiver(post_save, sender=User)
def save_user_profile(sender,instance,**kwargs):
    instance.profile.save()

class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    content = models.CharField(max_length=200)
    stars = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(5)],default=0)
    date = models.CharField(max_length=50)

class ShopItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    cert_licencse = ContentTypeRestrictedFileField(upload_to='uploads/',content_types=['text/plain'],max_upload_size=5000,blank=True,null=True)
    data = ContentTypeRestrictedFileField(upload_to='uploads/',content_types=['image/jpg','image/jpeg','image/bmp','image/tga','image/png'],max_upload_size=5000,blank=True,null=True)

class ShopListing(models.Model):
    item = models.OneToOneField(ShopItem, on_delete=models.CASCADE)
    buyers = models.CharField(max_length=5000)
    price = models.FloatField(validators=[MinValueValidator(0.0),MaxValueValidator(1000000000)])
    description = models.CharField(max_length=300)
    sold = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(100)],default=0)
    reception = models.ForeignKey(Comment, on_delete=models.DO_NOTHING)

class ForumPost(models.Model):
    creator = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    content = models.CharField(max_length=500)
    date = models.CharField(max_length=50)

class ForumTopic(models.Model):
    creator = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    posts = models.ForeignKey(ForumPost,on_delete=models.CASCADE)
    creation_date = models.CharField(max_length=50)
    last_post = models.CharField(max_length=50)
    num_Posts = models.IntegerField()






    


