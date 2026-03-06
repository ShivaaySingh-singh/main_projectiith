import json
from decimal import Decimal
from django.db import transaction 
from django.db.models import Sum 
from django.core.exceptions import ValidationError

from .models import Receipt, ReceiptAllocation
from .models import Project, SeedGrant, TDGGrant

def detect_funding(short_no):

    project = Project.objects.filter(project_no=short_no).first()
    if project:
        return project, project.sanction_amount
    
    seed = SeedGrant.objects.filter(grant_no=short_no).first()
    if seed:
        return seed, seed.total_budget
    
    tdg = TDGGrant.objects.filter(grant_no=short_no).first()
    if tdg:
        return tdg, tdg.total_budget
    
    return None, None

def create_receipt_with_allocations(form, allocations_data):

    short_no= form.cleaned_data["short_no"]
    new_total = form.cleaned_data["total_amount"]

    with transaction.atomic():
        funding_obj, sanction_amount = detect_funding(short_no)

        if not funding_obj:
            raise ValidationError("Invalid Project/ Grant Number.")
        
        funding_obj = funding_obj.__class__.objects.select_for_update().get(pk=funding_obj.pk)
        
        existing_total = Receipt.objects.filter(
            short_no = short_no
        ).aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0")

        if existing_total + new_total > sanction_amount:
            raise ValidationError(
                "Receipt exceeds sanctioned amount."
            )
        
        allocation_sum = sum(Decimal(str(item["amount"])) for item in allocations_data)

        if allocation_sum != new_total:
            raise ValidationError(
                "Head allocation total must match receipt total."
            ) 
        receipt = form.save()

        for item in allocations_data:
            ReceiptAllocation.objects.create(
                receipt=receipt,
                head_id=item["head"],
                amount=item["amount"]
            )
        return receipt
