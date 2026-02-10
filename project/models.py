from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from datetime import date 
from django.core.validators import MinValueValidator
import re
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


fy_validator = RegexValidator(
    regex=r'^\d{4}-\d{2}$',
    message = "Financial year must be in format YYYY-YY, e.g. 2024-25"
)
def validate_positive_amount(value):
        """Ensure amount is positive and numeric only"""
        if value < 0:
            raise ValidationError('Amount cannot be negative. Only positive values are allowed.')
        return value

class Faculty(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,related_name='faculty', on_delete=models.CASCADE, null=True, blank=True)
    faculty_id = models.CharField(max_length=50, unique=True, primary_key=True)  # Excel: Faculty ID
    pi_name = models.CharField(max_length=255)  # Excel: PI Name
    email = models.EmailField(blank=True, null=True)  # Excel: PI Email ID
    designation = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)  # Excel: Dept.
    photo = models.ImageField(upload_to='faculty_photos/', blank=True, null=True)

    

    def __str__(self):
        return self.pi_name
    class Meta:
        verbose_name = "Faculty Member"
        verbose_name_plural = "Faculty Members"

class CoPiName(models.Model):
    faculty_id = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=150)
    email= models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.faculty_id})"
    class Meta:
        ordering = ["name"]
    
class Project(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ONGOING', 'Ongoing'),
        ('CLOSED', 'Closed'),
    ]
    
    
    
    # Primary and Unique Fields
    project_short_no = models.CharField(max_length=50, unique=True,)
    project_no = models.CharField(max_length=100, unique = True)
    gender = models.CharField(max_length=7, choices=GENDER_CHOICES)
    project_type = models.CharField(max_length=100,verbose_name="Project Type")
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="projects")
    pi_name = models.CharField(max_length=100)
    co_pi_name = models.ForeignKey(
        CoPiName,on_delete=models.SET_NULL, null=True, blank=True,
        related_name="projects_as_copi"
    )

    dept = models.CharField(max_length=100, blank=True, null=True
                            
                            )
        
    # Project Details
    project_title = models.TextField(
        verbose_name="Project Title",
        
    )
    
    # Sponsoring Agency Details
    gst_no = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name="GST No."
    )
    address_sponsoring_agency = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Address of Sponsoring Agency"
    )
    pincode = models.CharField(
        max_length=10, 
        blank=True, 
        null=True,
        verbose_name="Pincode"
    )
    sponsoring_agency = models.CharField(
        max_length=300,
        verbose_name="Sponsoring Agency"
    )
    country = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Country"
    )
    
    # Duration and Dates
    
    project_start_date = models.DateField(
        verbose_name="Project Start Date",
        
    )
    project_end_date = models.DateField(
        verbose_name="Project End Date",
        
    )
    
    
    # Fellow/Student Information
    fellow_student_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Fellow/Student Name"
    )
    
    # Scheme Information
    scheme_code = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Scheme Code"
    )
    scheme_name = models.CharField(
        max_length=300, 
        blank=True, 
        null=True,
        verbose_name="Scheme Name"
    )
    
    # Sanction Details
    sanction_number = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Sanction Number/MOU/Agreement"
    )
    sanction_date = models.DateField(
        verbose_name="Sanction Date",
        
    )
    sanction_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0), validate_positive_amount],
        verbose_name="Sanction Amount",
        
    )
    
    # Financial Details
    amount_to_be_received = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0), validate_positive_amount],
        verbose_name="Amount to be Received by Sponsoring Agency",
        
    )
    total_non_recurring = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0), validate_positive_amount],
        verbose_name="Total Non-Recurring",
        
    )
    total_recurring = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(0), validate_positive_amount],
        verbose_name="Total Recurring",
        
    )
    
    # Bank Details
    bank_name_account = models.CharField(
        max_length=300, 
        blank=True, 
        null=True,
        verbose_name="Bank Name & A/C No."
    )
    
    # Additional Information
    remarks = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Remarks"
    )

    project_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ONGOING',
        verbose_name="Project Status"
    )

    is_extended = models.BooleanField(default=False, verbose_name="Is Project Extended")
    extended_end_date = models.DateField(null=True, blank =True, verbose_name="Extended End Date")
    

    extension_reason = models.TextField(null=True, blank=True, verbose_name="Extension Reason")

    extension_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_project_extension"
    )
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-project_start_date']

    def get_effective_end_date(self):
        if self.is_extended and self.extended_end_date:
            return self.extended_end_date
        return self.project_end_date
    
    @property

    def duration(self):
        start = self.project_start_date
        end = self.final_end_date

        if not start or not end:
            return None
        
        if end < start:
            return None
        
        months = (end.year - start.year) * 12 + (end.month - start.month)

        if end.day < start.day:
            months -= 1 

        years = months // 12
        rem_months = months % 12

        result = []

        if years > 0:
            result.append(f"{years} year" if years == 1 else f"{years} years")

        if rem_months > 0:
            result.append(f"{rem_months} month" if rem_months == 1 else f"{rem_months} months")

        if not result:
            return "0 months"

        return " ".join(result)  



    @property
    def final_end_date(self):
        return self.get_effective_end_date()
    def clean(self):
        """Additional validation for amount fields"""
        super().clean()
        
        # Validate all amount fields
        amount_fields = [
            ('sanction_amount', self.sanction_amount),
            ('amount_to_be_received', self.amount_to_be_received),
            ('total_non_recurring', self.total_non_recurring),
            ('total_recurring', self.total_recurring),
        ]
        
        for field_name, value in amount_fields:
            if value is not None and value < 0:
                raise ValidationError({
                    field_name: 'Only positive amounts are allowed. Negative values are not permitted.'
                })
            
        if self.is_extended:
            if not self.extended_end_date:
                raise ValidationError({"extended_end_date": "Extended end date is required if project is extended"})
            
            if self.extended_end_date <= self.project_end_date:
                raise ValidationError({"extended_end_date": "Extended end date must be greater than the original end date"})
        else:
            if self.extended_end_date:
                raise ValidationError({
                    "extended_end_date": "Cannot set extended date if project is not marked as extended."
                })   
    
    def save(self, *args, **kwargs):

        if self.faculty:
            if not self.pi_name:
                self.pi_name = self.faculty.pi_name
            if not self.dept:
                self.dept = self.faculty.department
        # Run full validation before saving
        self.full_clean()
        
        # Auto-update project status based on end date
        
        today = date.today()
        effective_end = self.get_effective_end_date()

        if effective_end < today:
            self.project_status = 'CLOSED'
        else:
            self.project_status = 'ONGOING'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.project_short_no

class ReceiptHead(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Receipt Head"
        verbose_name_plural = "Receipt Heads"
        ordering = ["name"]   

    def __str__(self):
        return self.name 




# ✅ Custom Manager for handling superuser and users
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field is required")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        if extra_fields.get("role") is None:
            user.role = "faculty"
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")  # 👈 superuser always admin role
        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('faculty', 'Faculty'),
        ('admin', 'Admin Member'),
        ('sheet', 'SheetUser')

    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='faculty')
    
    objects = CustomUserManager()
    
    def save(self, *args, **kwargs):
        #If Superser then dont change 
        if self.is_superuser:
            self.is_staff = True
        else:
            # For Faculty
            if self.role == 'faculty':
                self.is_staff = False
                self.is_superuser = False

            # Admin member ke liye
            elif self.role == 'admin':
                self.is_staff = True
                self.is_superuser = False
        
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "Users"

class SeedGrant(models.Model):
    grant_no = models.CharField(max_length=100, unique=True)
    short_no = models.CharField(max_length=50, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="seed_grants")
    pi_name = models.CharField(max_length=255)
    dept = models.CharField(max_length=100)
    title = models.TextField()
    sanction_date = models.DateField()
    end_date = models.DateField()

    budget_year1 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    budget_year2 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
   
    equipment = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    consumables = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    contingency = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    travel = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    manpower = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    others = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    furniture = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    visitor_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    lab_equipment = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    is_extended = models.BooleanField(default=False)
    extended_end_date = models.DateField(null=True, blank=True)
    extension_reason = models.TextField(null=True, blank=True)
    extension_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_seed_extensions"
    )
    project_status = models.CharField(
        max_length=20,
        choices=(
            ("ONGOING", "Ongoing"),
            ("EXPIRED", "Expired")
        ),
        default="ONGOING"

    )

    def get_effective_end_date(self):
        if self.is_extended and self.extended_end_date:
            return self.extended_end_date
        return self.end_date
    
    @property
    def final_end_date(self):
        return self.get_effective_end_date()
    
    def save(self, *args, **kwargs):
        
        if self.faculty:
            self.pi_name = self.faculty.pi_name
            self.dept = self.faculty.department
        
        self.full_clean()

        today = date.today()
        effective_end = self.get_effective_end_date()

        if today > effective_end:
            self.project_status = "EXPIRED"
        else:
            self.project_status = "ONGOING"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.short_no
    
    def clean(self):
        if self.is_extended:
            if not self.extended_end_date:
                raise ValidationError("Extended end date is required when project is extended.")
            
            if self.extended_end_date <= self.end_date:
                raise ValidationError("Extended end date must be greater than original end date.")
        
    
    class Meta:
        verbose_name = "Seed Grant"
        verbose_name_plural = "Seed Grants"

class TDGGrant(models.Model):
    grant_no = models.CharField(max_length=100, unique=True )
    short_no = models.CharField(max_length=50, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name="tdg_grants")
    pi_name = models.CharField(max_length=255)
    co_pi = models.CharField(max_length=255, blank=True, null=True)
    dept = models.CharField(max_length=100)
    title = models.TextField()
    industry_partner = models.CharField(max_length=200, blank=True, null=True)
    industry_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sanction_date = models.DateField()
    end_date = models.DateField()

    budget_year1 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    budget_year2 = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    equipment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    consumables = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    contingency = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    travel = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manpower = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    others = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    furniture = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_extended = models.BooleanField(default=False)
    extended_end_date = models.DateField(null=True, blank=True)
    extension_reason = models.TextField(null=True, blank=True)
    extension_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_tdg_extensions"
    )
    project_status = models.CharField(
        max_length=20,
        choices=(
            ("ONGOING", "Ongoing"),
            ("EXPIRED", "Expired")
        ),
        default="ONGOING"

    )

    def get_effective_end_date(self):
        if self.is_extended and self.extended_end_date:
            return self.extended_end_date
        return self.end_date
    
    @property
    def final_end_date(self):
        return self.get_effective_end_date()

    def save(self, *args, **kwargs):
        
        if self.faculty:
            self.pi_name = self.faculty.pi_name
            self.dept = self.faculty.department
        
        self.full_clean()
        
        today = date.today()
        effective_end = self.get_effective_end_date()

        if today > effective_end:
            self.project_status = "EXPIRED"
        else:
            self.projectstatus = "ONGOING"
        super().save(*args, **kwargs)

    def clean(self):
        if self.is_extended:
            if not self.extended_end_date:
                raise ValidationError("Extended end date is required when project is extended.")

            if self.extended_end_date <= self.end_date:
                raise ValidationError("Extended end date must be greater than original end date.")
        
    def __str__(self):
        return self.short_no
    
    class Meta:
        verbose_name = "TDG Grant"
        verbose_name_plural = "TDG Grants"
# For inward supporting table of TDSSection and TDSRate
class TDSSection(models.Model):
    section = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.section
    

class TDSRate(models.Model):
    section = models.ForeignKey(TDSSection, on_delete=models.CASCADE, related_name="tds_rates")
    percent = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.percent}%"
    
class BillInward(models.Model):
    BILL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('returned', 'Returned'),
    ]
     
    date = models.DateField(verbose_name="Date")
    received_from = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="Name of Person / Received From"
    )
    faculty = models.ForeignKey(
        'Faculty',  # Links to Faculty model
        on_delete=models.PROTECT,  # Prevents deleting faculty if bills exist
        related_name='inward_bills',
        verbose_name="Faculty",
        to_field='faculty_id',  
    )

    pi_name = models.CharField(
        max_length=255,
        verbose_name="Name of the Considered Faculty",
        blank=True,
        help_text="Auto-filled from Faculty table"
    )
    project_no = models.CharField(max_length=100,blank=True,null=True,verbose_name="Project No.")
    particulars = models.TextField(verbose_name="Particulars")
    amount = models.DecimalField(max_digits=12,decimal_places=2,verbose_name="Amount (in Rs.)")
    under_head = models.CharField(max_length=100,blank=True,null=True,verbose_name="Under Head")
    po_no = models.CharField(max_length=100,blank=True,null=True,verbose_name="PO No.")
    tds_section =models.ForeignKey(TDSSection, on_delete=models.SET_NULL, null=True, blank=True)
    tds_rate = models.ForeignKey(TDSRate, on_delete=models.SET_NULL, null=True, blank=True)
    tds_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places =2, default=0)
    # Assignment & Status
    whom_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                limit_choices_to={'role': 'admin'}, related_name='assigned_bills',
                                verbose_name="Assigned To (Admin Member)")
    
    outward_date = models.DateField(blank=True,null=True,verbose_name="Outward Date")
    
    bill_status = models.CharField(max_length=20,choices=BILL_STATUS_CHOICES,default='pending',verbose_name="Bill Status")

    bill_pdf = models.FileField(upload_to="bill_pdfs/", null=True, blank=True, verbose_name="Bill PDF")

    remarks = models.TextField(
        blank=True,
        null=True,
        verbose_name="Remarks")
    
    class Meta:
        verbose_name = "Bill Inward"
        verbose_name_plural = "Bill Inwards"
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['faculty']),
            models.Index(fields=['whom_to']),
            models.Index(fields=['bill_status']),
        ]
    def __str__(self):
        return f"{self.pi_name or self.faculty.pi_name} - {self.date} - Rs.{self.amount}"
    
    def save(self, *args, **kwargs):
        """Auto-fill faculty_name from Faculty FK on save"""
        if self.faculty and not self.pi_name:
            self.pi_name = self.faculty.pi_name
        super().save(*args, **kwargs)
    
    @property
    def faculty_id_display(self):
        """Access faculty ID through FK"""
        return self.faculty.faculty_id if self.faculty else ""

class Expenditure(models.Model):
    id = models.AutoField(primary_key=True)

    date = models.DateField()

    bill_date = models.DateField(blank=True, null=True)

    seed_grant = models.ForeignKey(
        SeedGrant,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='expenditures'
    )

    tdg_grant = models.ForeignKey(
        TDGGrant,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='expenditures_tdg'
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="expenditures"
    )

    voucher_no =models.CharField(max_length=100, null=True, blank=True)

    
    
    head = models.CharField(max_length=100)
    particulars = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)
    
    def clean(self):
        funding = self.seed_grant or self.tdg_grant or self.project

        if not funding:
            raise ValidationError("Select exactly one funding source.")

        if sum(bool(x) for x in [self.seed_grant, self.tdg_grant, self.project]) != 1:
            raise ValidationError("Select only one funding source.")

        effective_end = funding.get_effective_end_date()

        if self.bill_date > effective_end:
            raise ValidationError(
                f"Funding expired on {effective_end}. Entry date not allowed."
            )

        if getattr(funding, "project_status", None) in ["CLOSED", "EXPIRED"]:
            raise ValidationError("Funding source is not active.")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    

    @property
    
    def grant_no(self):
        """Returns grant_no from related grant"""
        if self.seed_grant:
            return self.seed_grant.grant_no
        elif self.tdg_grant:
            return self.tdg_grant.grant_no
        return None
    
    @property
    def short_no(self):
        """Returns short_no from related grant"""
        if self.seed_grant:
            return self.seed_grant.short_no
        elif self.tdg_grant:
            return self.tdg_grant.short_no
        return None



    def __str__(self):
        code = self.short_no or "—"
        return f"{code} | {self.head} | {self.amount}"
    
    class Meta:
        verbose_name = "Expenditure"
        verbose_name_plural = "Expenditures"


# ✅ Commitment
class Commitment(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    bill_date =models.DateField(blank=True, null=True)
    
    seed_grant = models.ForeignKey(
        SeedGrant,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='commitments'
    )

    tdg_grant = models.ForeignKey(
        TDGGrant,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='commitments_tdg'
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="commitments"
    )

    voucher_no = models.CharField(
        max_length=100,
        null=True, blank=True
    )
    
    
    head = models.CharField(max_length=100)
    particulars = models.TextField()
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)

    def clean(self):
        funding = self.seed_grant or self.tdg_grant or self.project

        if not funding:
            raise ValidationError("Select exactly one funding source.")

        if sum(bool(x) for x in [self.seed_grant, self.tdg_grant, self.project]) != 1:
            raise ValidationError("Select only one funding source.")

        effective_end = funding.get_effective_end_date()

        if self.bill_date > effective_end:
            raise ValidationError(
                f"Funding expired on {effective_end}. Entry date not allowed."
            )

        if getattr(funding, "project_status", None) in ["CLOSED", "EXPIRED"]:
            raise ValidationError("Funding source is not active.")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    

    @property
    def grant_no(self):
        if self.seed_grant:
            return self.seed_grant.grant_no
        elif self.tdg_grant:
            return self.tdg_grant.grant_no
        return None
    
    @property
    def short_no(self):
        if self.seed_grant:
            return self.seed_grant.short_no
        elif self.tdg_grant:
            return self.tdg_grant.short_no
        return None

    def __str__(self):
        code = self.short_no or "—"
        return f"{code} | {self.head} | {self.gross_amount}"
    
    class Meta:
        verbose_name = "Commitment"
        verbose_name_plural = "Commitments"
  
class FundRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    request_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    faculty = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name='fund_requests')
    pi_name = models.CharField(max_length=200)
    

    #roject selection - can be Project, seedGrant , or TDGGrant

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True, related_name='fund_requests'
    )

    seed_grant = models.ForeignKey(
        SeedGrant,
        on_delete=models.CASCADE,
        null= True,
        blank = True,
        related_name='fund_requests'
    )

    tdg_grant = models.ForeignKey(
        TDGGrant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fund_requests'
    )

    project_no = models.CharField(max_length=100)
    grant_no = models.CharField(max_length=100, blank=True, null=True)
    short_no = models.CharField(max_length=100)
    project_title = models.CharField(max_length=500)

    head = models.CharField(max_length=200, help_text="Expense head/category")
    particulars = models.TextField(help_text="Details of expense")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks_by_src = models.TextField(blank=True, null=True, verbose_name="Remarks by SRC")

    class Meta:
        ordering = ['-request_date']
        verbose_name = "Fund Request"
        verbose_name_plural = "Fund Requests"

    def __str__(self):
        return f"{self.pi_name} - {self.project_no} - {self.status}"
    
    def clean(self):
        selected = sum([
            bool(self.project),
            bool(self.seed_grant),
            bool(self.tdg_grant)
        ])
        if selected != 1:
            raise ValidationError("please select exactly one project/grant type.")
        

class Receipt(models.Model):
    
    receipt_date = models.DateField(blank=True, null=True)
    
    seed_grant = models.ForeignKey(SeedGrant, on_delete=models.CASCADE, null=True, blank=True, related_name='receipts')

    tdg_grant = models.ForeignKey(TDGGrant, on_delete=models.CASCADE, null=True, blank=True, related_name='receipts_tdg')

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="receipts")

    date = models.DateField(blank=True, null=True)                     
    
    category = models.CharField(max_length=100, blank=True, null=True)           
    reference_number = models.CharField(max_length=100, blank=True, null=True)   
    
    # sanction heads (fixed)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    head = models.ForeignKey(ReceiptHead,on_delete=models.PROTECT,null=True, blank=True, related_name="receipts")

    def clean(self):
        funding = self.seed_grant or self.tdg_grant or self.project

        if not funding:
            raise ValidationError("Select exactly one funding source.")

        if sum(bool(x) for x in [self.seed_grant, self.tdg_grant, self.project]) != 1:
            raise ValidationError("Select only one funding source.")

        if self.receipt_date:
            effective_end = funding.get_effective_end_date()

            if self.receipt_date > effective_end:
                raise ValidationError(
                    f"Funding expired on {effective_end}. Receipt date not allowed."
            )

        if getattr(funding, "project_status", None) in ["CLOSED", "EXPIRED"]:
            raise ValidationError("Funding source is not active.")

        

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.project:
            code = self.project.project_no
        elif self.seed_grant:
            code = self.seed_grant.grant_no
        else:
            code = "-"
        return f"{code} | {self.amount}"
    
    class Meta:
        verbose_name = "Receipt"
        verbose_name_plural = "Receipts"
        ordering = ["receipt_date"]


    

        

    
class ProjectSanctionDistribution(models.Model):
    """
    Head-wise and Year-wise distribution of sanctioned amount for a project.
    actins as budget distribution
    """
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE,null=True, blank=True, related_name = 'sanction_distributions')

    
    
    financial_year = models.CharField(max_length=7,validators=[fy_validator], help_text="e.g. 2024-25")
    
    project_year = models.PositiveSmallIntegerField(null=True, blank=True,
        help_text="1 = Year-1, 2 = Year-2, etc."
    )

    head = models.ForeignKey(
        ReceiptHead, on_delete=models.PROTECT, related_name="sanction_distributions",
        verbose_name="Sanction Head"
    )

    sanctioned_amount = models.DecimalField(max_digits=15, decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Sanctioned Amount"
    )

   
    

    remarks = models.TextField(blank=True, null=True)

    def clean(self):
        if not self.project:
            raise ValidationError({"project": "Project is required."})

        if self.project_year and self.project_year < 1:
            raise ValidationError({"project_year": "Project year must be >= 1"})
    
    
    def save(self, *args, **kwargs):
        
        
        self.full_clean()
        super().save(*args, **kwargs)

    

    class Meta:
        verbose_name = "Project Sanction Distribution"
        verbose_name_plural = "Project Sanction Distributions"
        constraints = [
            models.UniqueConstraint(
                fields=["project",  "financial_year", "project_year", "head"],
                name="unique_sanction_distribution"
            )
        ]

    def __str__(self):
        project_no = self.project.project_no if self.project else "-"
        return f"{project_no} | {self.financial_year} | Year-{self.project_year}"

# Payee an independent able keeping the records of employee

class Payee(models.Model):
    payee_type = models.CharField(max_length=20)
    name_of_payee = models.CharField(max_length=200)
    emp_code = models.CharField(max_length=50, blank=True, null=True)
    designation = models.CharField(max_length=100,blank=True,null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    pan = models.CharField(max_length=20, blank=True,null=True)
    gst = models.CharField(max_length=20,blank=True, null=True)

    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=200)
    branch = models.CharField(max_length=200)
    ifsc = models.CharField(max_length=20)

    email = models.EmailField()
    contact_no = models.CharField(max_length=20,blank=True, null=True)
    pfms_code = models.CharField(max_length=50, blank=True, null=True)
    pfms_name = models.CharField(max_length=200,blank=True, null=True)

    

    class Meta:
        verbose_name = "Payee"
        verbose_name_plural = "Payees"
        ordering = ["name_of_payee"]

    def __str__(self):
        return f"{self.name_of_payee} ({self.payee_type })"
    
class PaymentType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True

    )

    class Meta:
        verbose_name = "Payment Type"
        verbose_name_plural = "Payment Types"
        ordering = ["name"]

    def __str__(self):
        return self.name
    
class Bank(models.Model):
    bank_name = models.CharField(max_length=200, help_text="Full bank name")
    short_no = models.CharField(max_length=50, help_text="Short name / code used internally")
    account_no = models.CharField(max_length=50, help_text="Default / reference account number", blank=True, null=True)
    scheme_code = models.CharField(max_length=50, blank=True, null=True, help_text="Scheme code (if applicable)")

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "banks"
        ordering = ["bank_name"]
        unique_together = ("bank_name","short_no")

    def __str__(self):
        return f"{self.bank_name} ({self.short_no})"
    
GST_TDS_CHOICES = [
    ("CGST", "CGST @ 2%"),
    ("SGST", "SGST @ 2%"),
    ("IGST", "IGST @ 2%"),

]
PAYMENT_STATUS_CHOICES = [
    ("PROCESSED", "Processed"),
    ("PAID", "Paid"),
]

class Payment(models.Model):
    
    seed_grant = models.ForeignKey(SeedGrant, on_delete=models.CASCADE, null=True, blank=True, related_name="payments")

    tdg_grant = models.ForeignKey(TDGGrant, on_delete=models.CASCADE, null=True, blank=True, related_name ="payments")

    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name="payments")
    
    
    date = models.DateField()
    
    
    head = models.ForeignKey(ReceiptHead, on_delete=models.PROTECT, related_name="payments")

    # Payee Info
    payment_type = models.ForeignKey(PaymentType, on_delete=models.PROTECT,related_name="payments")
    payee = models.ForeignKey(Payee, on_delete=models.PROTECT,null =True, blank =True ,related_name="payments")

    bank = models.ForeignKey(Bank, on_delete=models.PROTECT,null=True,blank=True, related_name="payments")

    # Bank Info
    cheque_no = models.CharField(max_length=100, blank=True, null=True)
    utr_no = models.CharField(max_length=100, blank=True, null=True)

    payee_bank_name = models.CharField(max_length=50, blank=True, null=True)
    
    payee_branch_name = models.CharField(max_length=200, blank=True, null=True)
    payee_account_no = models.CharField(max_length=50, blank=True, null=True)
    payee_ifsc = models.CharField(max_length=20, blank=True, null=True)
    payee_pan = models.CharField(max_length=20, blank=True, null=True)

    # Transaction Info
    
    
    pi_name = models.CharField(max_length=200, blank=True, null=True)
    pi_email = models.EmailField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    # TDS Handling (Cascading Dropdowns in AG Grid)
    tds_section = models.ForeignKey(
        TDSSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tax U/S",
        related_name="payments"
    )

    tds_rate = models.ForeignKey(
        TDSRate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="TDS %",
        related_name="payments"
    )

    tds_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # GST-TDS
    gst_tds_type = models.CharField(max_length=20, choices=GST_TDS_CHOICES, blank=True, null=True)
    igst_tds = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cgst_tds = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    sgst_tds = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    # Final Calculated Amounts (Filled from AG Grid)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    purpose = models.TextField(blank=True, null=True)

    payee_email = models.EmailField(blank=True, null=True)
    other_email = models.EmailField(blank=True, null=True)
    cc_email_default = models.EmailField(blank=True, null=True)
    cc_email_po_store = models.EmailField(blank=True, null=True)

    payment_status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default="PROCESSED"
    )

    email_sent_log = models.TextField(
        blank=True,
        null=True,
        help_text="Auto-filled when paymentemail is sent"
    )

    
    def clean(self):
        errors = {}

        funding = self.seed_grant or self.tdg_grant or self.project

        if not funding:
            errors["__all__"] = "Select exactly one funding source."

        if sum(bool(x) for x in [self.seed_grant, self.tdg_grant, self.project]) != 1:
            errors["__all__"] = "Only one funding source is allowed."

        if self.date:
            effective_end = funding.get_effective_end_date()
            if self.date > effective_end:
                errors["date"] = (
                    f"Funding expired on {effective_end}. Payment date not allowed."
                )

        if getattr(funding, "project_status", None) in ["CLOSED", "EXPIRED"]:
            errors["__all__"] = "Funding source is not active."

        if not self.payee:
            errors["payee"] = "Payee is mandatory."

        if not self.bank:
            errors["bank"] = "Bank is mandatory."

        if errors:
            raise ValidationError(errors)
    


    def save(self, *args, **kwargs):
        funding = self.seed_grant or self.tdg_grant or self.project

        if funding:
            self.pi_name = getattr(funding, "pi_name", None)
            faculty = getattr(funding, "faculty", None)
            self.pi_email = faculty.email if faculty and faculty.email else None

        if self.payee:
            self.payee_email = self.payee.email

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.project:
            code = self.project.project_short_no
        elif self.seed_grant:
            code = self.seed_grant.short_no
        elif self.tdg_grant:
            code = self.tdg_grant.short_no
        else:
            code = "-"
        return f"{code} | {self.net_amount}"

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ["date"]

