from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Faculty(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    faculty_id = models.CharField(max_length=50, unique=True, blank=False, null=False)  # Excel: Faculty ID
    pi_name = models.CharField(max_length=255)  # Excel: PI Name
    email = models.EmailField(blank=True, null=True)  # Excel: PI Email ID
    designation = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)  # Excel: Dept.
    photo = models.ImageField(upload_to='faculty_photos/', blank=True, null=True)

    def __str__(self):
        return self.pi_name
    
class Project(models.Model):
    gender = models.CharField(max_length=10, blank=True, null=True)              
    type_of_project = models.CharField(max_length=100, blank=True, null=True)    
    project_no = models.CharField(max_length=100, unique=True)                   
    short_no = models.CharField(max_length=50, blank=True, null=True)            
    project_year = models.CharField(max_length=10, blank=True, null=True)        

    faculty_id = models.CharField(max_length=50, blank=False, null=False)          
    pi_name = models.CharField(max_length=255, blank=True, null=True)            
    pi_email = models.EmailField(blank=True, null=True)                          

    agency = models.CharField(max_length=255, blank=True, null=True)             
    department = models.CharField(max_length=255, blank=True, null=True)         
    project_title = models.CharField(max_length=500, blank=True, null=True)      
    duration = models.CharField(max_length=50, blank=True, null=True)            
    start_date = models.DateField(blank=True, null=True)                         
    end_date = models.DateField(blank=True, null=True)                           

    sponsoring_agency = models.CharField(max_length=255, blank=True, null=True)  
    sanction_no = models.CharField(max_length=100, blank=True, null=True)        
    sanction_date = models.DateField(blank=True, null=True)                      

    amount_to_be_received = models.FloatField(default=0)                         
    total_non_recurring = models.FloatField(default=0)                           
    total_recurring = models.FloatField(default=0)                               

    def __str__(self):
        return f"{self.project_no} - {self.project_title}"


class Receipt(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="receipts")
    receipt_date = models.DateField(blank=True, null=True)                       
    fy = models.CharField("Financial Year", max_length=20, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)           
    reference_number = models.CharField(max_length=100, blank=True, null=True)   

    # sanction heads (fixed)
    amount = models.FloatField(default=0)
    overhead = models.FloatField(default=0)
    equipment = models.FloatField(default=0)
    manpower = models.FloatField(default=0)
    consumables = models.FloatField(default=0)
    travel = models.FloatField(default=0)
    slf = models.FloatField("SLF@3%", default=0)
    contingency = models.FloatField(default=0)
    gst_consultancy = models.FloatField(default=0)
    tds_receivables = models.FloatField(default=0)

    def __str__(self):
        return f"{self.project.project_no} - {self.reference_number}"


    

        


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

class SeedGrant(models.Model):
    grant_no = models.CharField(max_length=100, primary_key=True)
    short_no = models.CharField(max_length=50, unique=True)
    faculty_id = models.CharField(max_length=50, blank=False, null=False)
    name = models.CharField(max_length=255)
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

    def __str__(self):
        return f"Seed {self.grant_no} - {self.name}"
class TDGGrant(models.Model):
    grant_no = models.CharField(max_length=100, primary_key=True)
    short_no = models.CharField(max_length=50, unique=True)
    faculty_id = models.CharField(max_length=50, blank=False, null=False)
    name = models.CharField(max_length=255)
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

    def __str__(self):
        return f"TDG {self.grant_no} - {self.name}"


class Expenditure(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()

    seed_grant = models.ForeignKey(
        SeedGrant,
        to_field='short_no',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='expenditures'
    )

    tdg_grant = models.ForeignKey(
        TDGGrant,
        to_field='short_no',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='expenditures_tdg'
    )

    short_no = models.CharField(max_length=50, blank=True, null=True)
    
    head = models.CharField(max_length=100)
    particulars = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Keep grant_no and short_no consistent if linked to a grant"""
        if self.seed_grant:
            self.short_no = self.seed_grant.short_no
            
        elif self.tdg_grant:
            self.short_no = self.tdg_grant.short_no
            
        super().save(*args, **kwargs)

    @property
    def grant_no(self):
        if self.seed_grant:
            return self.seed_grant.grant_no
        elif self.tdg_grant:
            return self.tdg_grant.grant_no
        return None


    def __str__(self):
        code = self.short_no or "—"
        return f"{code} | {self.head} | {self.amount}"


# ✅ Commitment
class Commitment(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    
    seed_grant = models.ForeignKey(
        SeedGrant,
        to_field='short_no',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='commitments'
    )

    tdg_grant = models.ForeignKey(
        TDGGrant,
        to_field='short_no',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='commitments_tdg'
    )


    short_no = models.CharField(max_length=50)
    
    head = models.CharField(max_length=100)
    particulars = models.TextField()
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Keep grant_no and short_no consistent if linked"""
        if self.seed_grant:
            self.short_no = self.seed_grant.short_no
            self.grant_no = self.seed_grant.grant_no
        elif self.tdg_grant:
            self.short_no = self.tdg_grant.short_no
            self.grant_no = self.tdg_grant.grant_no
        super().save(*args, **kwargs)

    @property
    def grant_no(self):
        if self.seed_grant:
            return self.seed_grant.grant_no
        elif self.tdg_grant:
            return self.tdg_grant.grant_no
        return None

    def __str__(self):
        code = self.short_no or "—"
        return f"{code} | {self.head} | {self.gross_amount}"


        

