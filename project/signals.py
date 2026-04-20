from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import EmailMessage
from django.forms.models import model_to_dict
from .models import AuditLog
from .tasks import send_payment_email_task

from .models import Payment

@receiver(post_save, sender=Payment)
def send_payment_email(sender, instance, **kwargs):

    if instance.payment_status == "PAID" and not instance.email_sent_log:
        send_payment_email_task.delay(instance.id)


    
    


TRACK_MODELS = ["Payment", "Commitment", "Expenditure"]

def get_changes(old, new):
    changes = {}

    for field in new._meta.fields:
        field_name = field.name

        old_value = getattr(old, field_name, None)
        new_value = getattr(new, field_name, None)

        if old_value != new_value:
            changes[field_name] = {
                "old": str(old_value),
                "new": str(new_value)
            }

    return changes

@receiver(pre_save)
def store_old_instance(sender, instance, **kwargs):
    if sender.__name__ not in TRACK_MODELS:
        return

    if instance.pk:
        try:
            instance._old_instance = sender.objects.get(pk=instance.pk)  
        except sender.DoesNotExist:
            instance._old_instance = None

@receiver(post_save)
def log_create_update(sender, instance, created, **kwargs):
    if sender.__name__ not in TRACK_MODELS:
        return
    

    user = getattr(instance, "_current_user", None)

    

    if created:
        AuditLog.objects.create(
            user=user,
            model_name=sender.__name__,
            object_id=instance.pk,
            action="CREATE",
            changes={}
        )
    else:
        old = getattr(instance, "_old_instance", None)

        if old:
            changes = get_changes(old, instance)

            if changes:
                AuditLog.objects.create(
                    user=user,
                    model_name=sender.__name__,
                    object_id=instance.pk,
                    action="UPDATE",
                    changes=changes
                )

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender.__name__ not in TRACK_MODELS:
        return
    user = getattr(instance, "_current_user", None)

    AuditLog.objects.create(
        user=user,
        model_name=sender.__name__,
        object_id=instance.pk,
        action="DELETE",
        changes={}
    )
