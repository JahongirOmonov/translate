# from datetime import datetime
#
# from django.db.models.signals import pre_save
# from django.dispatch import receiver
#
# from utils import Profile
#
#
# @receiver(pre_save, sender=Profile)
# def update_updated_at(sender, instance, **kwargs):
#     print("qale")
#     instance.updated_at = datetime.now()
