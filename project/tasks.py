from celery import shared_task
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import Payment

@shared_task(bind=True, max_retries=3)
def send_payment_email_task(self, payment_id):

    try:
        instance = Payment.objects.get(pk=payment_id)

        if instance.payment_status != "PAID":
            return
        
        if instance.email_sent_log:
            return
        
        if not instance.payee_email:
            return
        
        subject = "SRC Project - Payment Confirmation"

        body = f"""
Dear Sir / Madam,

This is to inform you that a payment has been successfully processed.

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
            instance.cc_email_po_store,
            instance.pi_email
        ]))

        email = EmailMessage(
                subject=subject,
                body=body,
                from_email="noreply@admin.iith.ac.in",
                to=[to_email],
                cc=cc_list
        )


        email.send()

        log = (
            f"{timezone.now().strftime('%d-%b-%Y %H:%M')} - "
            f"sent to {to_email}"
        )

        if cc_list:
            log += f", cc:{', '.join(cc_list)}"


        instance.email_sent_log = log
        instance.save(update_fields=["email_sent_log"])

    except Exception as e:
        raise self.retry(exc=e, countdown=10)