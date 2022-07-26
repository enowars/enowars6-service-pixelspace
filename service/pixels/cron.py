from django.utils import timezone
from .models import Profile
import logging
import datetime

logging.basicConfig(filename="/var/log/clean_up.log",encoding='utf-8',level=logging.DEBUG)
def clean_up():
    profiles = Profile.objects.all()
    deleted = False
        
    for p in profiles:   
        username = p.user.username
        if username != 'root':
            if p.expiration_date < timezone.now():   
                if p.user.delete():
                    logging.debug(f" Deleted USER {username} at {datetime.datetime.now()}")
                    deleted = True
    if not deleted:
        logging.debug(f" CLEAN_UP JOB RAN AT {datetime.datetime.now()} but NO profiles where detected.")