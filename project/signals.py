from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.mail import EmailMessage

from .models import Payment

@receiver(post_save, sender=Payment)
def send_payment_email(sender, instance, **kwargs):
    """
    Send email ONLY when:
      payemnt status == 'PAID'
      email_sent_log is EMPTY
    """
    if instance.payment_status !="PAID":
        return
    
    if instance.email_sent_log:
        return
    
    if not instance.payee_email:
        return
    
    subject = "SRC Project - Paymnet Confirmation"

    body = f"""
Dear Sir / Madam,

This is to inform you that a payment has been successfully processed.bool

Project No: {instance.project.project_no}
Payee Name: {instance.name_of_payee}
Net Amount: Rs. {instance.net_amount}
UTR No: {instance.utr_no}
Paid Date: {instance.date}

Regards,
SRC Section
IIT Hyderabad
"""
    to_email = instance.payee_email

    cc_list = list(filter(None, [
        instance.other_email,
        instance.cc_email_default,
        instance.cc_email_po_store
    ]))

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email="noreply@admin.iith.ac.in",
            to=[to_email],
            cc=cc_list
        )

        email.send(fail_silently=False)

        log = (
            f"{timezone.now().strftime('%d-%b-%Y %H:%M')} - "
            f"sent to {to_email}"

        )

        if cc_list:
            log += f", cc:{', '.join(cc_list)}"

        Payment.objects.filter(pk=instance.pk).update(
            email_sent_log=log
        )
    except Exception as e:
        print("Payment mail failed:", e)