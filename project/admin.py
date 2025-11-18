from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.template.response import TemplateResponse
from import_export.admin import ImportExportModelAdmin
from .views import bill_report_admin
from django import forms
from .models import CustomUser, Faculty
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json  # ✅ ADD THIS - needed for JSON encoding
from .models import models
from .models import (
    Faculty, Project, Receipt, SeedGrant, TDGGrant,
    Expenditure, Commitment, CustomUser, FundRequest
)
from .resources import (
    ProjectResource, ReceiptResource, SeedGrantResource,
    TDGGrantResource, ExpenditureResource, CommitmentResource
)

from .utils import generate_random_password, send_credentials_email
from django.contrib import messages

HEADS = [
    "Equipment", "Consumables", "Contingency", "Travel",
    "Manpower", "Others", "Furniture", "Visitor Expenses", "Lab Equipment"
]


# =============================================================================
# 🆕 NEW: Excel View Mixin (Generic for all models)
# =============================================================================
class ExcelViewMixin:
    """
    ✅ Generic Excel View for any model
    Just inherit this mixin - Excel View ready!
    
    Usage:
        class MyModelAdmin(ExcelViewMixin, ImportExportModelAdmin):
            pass  # Done! Excel View available
    """
    
    excel_grant_fields = []  # Override if model has FK to grants
    excel_exclude_fields = ['id']  # Fields to hide in Excel view
    
    # ✅ ONE LINE - Auto-set template for ALL models
    change_list_template = 'admin/change_list_with_excel.html'
    
    def get_urls(self):
        """Add Excel View URL"""
        urls = super().get_urls()
        model_name = self.model._meta.model_name
        
        custom_urls = [
            path(
                'excel-view/', 
                self.admin_site.admin_view(self.excel_view),
                name=f'{model_name}_excel_view'
            ),
        ]
        return custom_urls + urls
    
    def excel_view(self, request):
        """Main Excel View - works for all models"""
        model_name = self.model.__name__
        fields_config = self.get_excel_fields_config()
        context_data = self.get_excel_context_data()
        
        context = {
            'model_name': model_name.lower(),
            'model_verbose_name': self.model._meta.verbose_name,
            'fields_config': json.dumps(fields_config),
            'has_grants': len(self.excel_grant_fields) > 0,
            **context_data,
            'title': f'{self.model._meta.verbose_name} - Excel View',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
        }
        
        return render(request, 'admin/generic_excel_view.html', context)
    
    def get_excel_fields_config(self):
        """Auto-detect model fields and create AG-Grid config"""
        fields = []
        
        for field in self.model._meta.fields:
            if field.name in self.excel_exclude_fields:
                continue

            if field.primary_key:
                is_editable = isinstance(field, (models.CharField, models.TextField))
            else:
                is_editable = True
            
            field_config = {
                'name': field.name,
                'label': field.verbose_name.title(),
                'type': field.get_internal_type(),
                'editable': is_editable,
                'required': not field.null and not field.blank,
                'width': self.get_field_width(field),
            }
            
            if field.choices:
                field_config['choices'] = [choice[0] for choice in field.choices]
            
            fields.append(field_config)
        
        return fields
    
    def get_field_width(self, field):
        """Auto-calculate column width based on field type"""
        field_type = field.get_internal_type()
        
        if field_type in ['TextField']:
            return 300
        elif field_type in ['DateField', 'DateTimeField']:
            return 130
        elif field_type in ['DecimalField', 'FloatField']:
            return 150
        else:
            return 180
    
    def get_excel_context_data(self):
        """
        Override this in subclass to add model-specific data
        
        Example:
            def get_excel_context_data(self):
                return {
                    'seed_grants': list(SeedGrant.objects.values(...)),
                    'heads': json.dumps(HEADS)
                }
        """
        return {}

# =============================================================================
# Custom Admin Site with Grouping (Existing - No changes)
# =============================================================================
class CustomAdminSite(admin.AdminSite):
    site_header = "IIT Hyderabad (SRC) - Admin Panel"
    site_title = "IIT Hyderabad SRC Admin"
    index_title = "Welcome to SRC Admin Dashboard"

    def get_app_list(self, request, app_label=None):
        """Custom grouping for admin sidebar"""
        custom_groups = {
            'Seed Grant': ['SeedGrant', 'TDGGrant', 'Expenditure', 'Commitment'],
            'Project Master': ['Project', 'Receipt'],
            'User Management': ['CustomUser', 'Faculty'],
            'Fund Request': ['FundRequest'],
           
        }

        app_dict = self._build_app_dict(request, app_label)
        custom_app_list = []

        for group_name, model_names in custom_groups.items():
            group_models = []
            for app_name, app_data in app_dict.items():
                for model in app_data['models']:
                    if model['object_name'] in model_names:
                        group_models.append(model)
                        
            if group_models:
                custom_app_list.append({
                    'name': group_name,
                    'app_label': group_name.lower().replace(' ', '_'),
                    'models': group_models,
                    'has_module_perms': True,
                })
        
        return custom_app_list
    
    def get_urls(self):
        """Override to add custom URLs"""
        urls = super().get_urls()
        custom_urls = [
            path(
                "project-fund-detail/",
                self.admin_view(project_fund_detail_view),
                name="project_fund_detail"
            ),
            path(
                "seed-grant-detail/",
                self.admin_view(seed_grant_detail_view),
                name="seed_grant_detail"
            ),
        ]
        return custom_urls + urls


def project_fund_detail_view(request):
    return TemplateResponse(request, "admin/fund_management.html", {})


def seed_grant_detail_view(request):
    return bill_report_admin(request)


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')


# =============================================================================
# Custom User Forms and Admin (Existing - No changes)
# =============================================================================
class CustomUserCreationForm(forms.ModelForm):
    """Custom form with auto-username from email and optional password"""
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        required=False,
        help_text='Leave blank to auto-generate a secure password'
    )
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput,
        required=False,
        help_text='Enter the same password as before, for verification'
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'role')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        
        if not username and email:
            username = email.split('@')[0]
            if CustomUser.objects.filter(username=username).exists():
                counter = 1
                while CustomUser.objects.filter(username=f"{username}{counter}").exists():
                    counter += 1
                username = f"{username}{counter}"
        
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if not password1 and not password2:
            return password2
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        
        if not password:
            password = generate_random_password()
        
        user.set_password(password)
        
        if commit:
            user.save()
        
        user._temp_password = password
        return user


class FacultyInline(admin.StackedInline):
    model = Faculty
    can_delete = False
    verbose_name_plural = "Faculty Details"
    fk_name = "user"
    extra = 0


class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    inlines = (FacultyInline,)
    exclude = ("groups", "user_permissions",)

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (("Personal info"), {"fields": ("first_name", "last_name")}),
        (("Role"), {"fields": ("role",)}),
        (("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role"),
        }),
    )
    list_display = ("username", "email", "role", "is_staff", "is_superuser")

    def save_model(self, request, obj, form, change):
        if not change:
            if 'password1' in form.cleaned_data and form.cleaned_data['password1']:
                password = form.cleaned_data['password1']
            else:
                password = generate_random_password()
                obj.set_password(password)

            super().save_model(request, obj, form, change)

            if obj.email:
                email_sent = send_credentials_email(obj, password, request)
                if email_sent:
                    messages.success(request, f'User "{obj.username}" created successfully. Credentials sent to {obj.email}')
                else:
                    messages.warning(request, f'User "{obj.username}" created but email failed. Password: {password}')
            else:
                messages.warning(request, f'User "{obj.username}" created but no email provided. Password: {password}')
        else:
            super().save_model(request, obj, form, change)


# =============================================================================
# 🆕 Model Admins with Excel View Mixin
# =============================================================================

# ✅ Simple Models (No grant relations)
class ProjectAdmin(ExcelViewMixin, ImportExportModelAdmin):
    """
    Project Admin:
        - Import/Export: ✅ (from ImportExportModelAdmin)
        - Excel View: ✅ (from ExcelViewMixin)
    """
    resource_class = ProjectResource
    list_display = ("project_no", "project_title", "start_date", "end_date", "pi_name")
    search_fields = ("project_no", "project_title", "pi_name")
    
    # ✅ No extra configuration needed - Excel View automatically works!


class ReceiptAdmin(ExcelViewMixin, ImportExportModelAdmin):
    resource_class = ReceiptResource
    list_display = ("project", "category", "amount", "equipment", "manpower", "consumables")
    search_fields = ("project__project_no", "category")


class SeedGrantAdmin(ExcelViewMixin, ImportExportModelAdmin):
    resource_class = SeedGrantResource
    list_display = ("grant_no", "short_no", "name", "dept", "total_budget")
    search_fields = ("grant_no", "short_no", "name")


class TDGGrantAdmin(ExcelViewMixin, ImportExportModelAdmin):
    resource_class = TDGGrantResource
    list_display = ("grant_no", "short_no", "name", "dept", "total_budget")
    search_fields = ("grant_no", "short_no", "name")

class ProjectAdmin(ExcelViewMixin, ImportExportModelAdmin):
    resource_class = ProjectResource
    list_display = (
        'project_short_no',
        'project_no',
        'pi_name',
        'project_title',
        'project_start_date',
        'project_end_date',
        'project_status',
        'sanction_amount',
    )
    search_fields = ('project_short_no', 'project_no', 'pi_name', 'project_title')
    list_filter = ('project_status', 'gender', 'project_type', 'department')
    readonly_fields = ('project_status',)


# ✅ Models with Grant Relations (Need extra configuration)
class ExpenditureAdmin(ExcelViewMixin, ImportExportModelAdmin):
    """
    Expenditure Admin:
        - Import/Export: ✅ (from ImportExportModelAdmin)
        - Excel View: ✅ (from ExcelViewMixin)
        - Grant Dropdowns: ✅ (custom configuration below)
    
    Changes from old code:
        ❌ Removed: expenditure_excel_view method (mixin handles it)
        ❌ Removed: get_urls override (mixin handles it)
        ✅ Added: excel_grant_fields (tells mixin about grants)
        ✅ Added: get_excel_context_data (provides grant data)
    """
    resource_class = ExpenditureResource
    list_display = ("grant_no", "head", "amount", "date")
    search_fields = ("short_no", "head")
    
    # ✅ Tell mixin that this model has grant fields
    excel_grant_fields = ['seed_grant', 'tdg_grant']
    
    # Hide short numberfrom excel view that is foreign key contains relation
    excel_exclude_fields = ['id', 'short_no', 'seed_grant', 'tdg_grant']
    
    def get_excel_context_data(self):
        """
        Provide grant data for dropdowns in Excel view
        JavaScript template will use this data
        """
        return {
            'seed_grants': list(SeedGrant.objects.values('short_no', 'grant_no', 'name')),
            'tdg_grants': list(TDGGrant.objects.values('short_no', 'grant_no', 'name')),
            'heads': json.dumps(HEADS),  # Convert list to JSON string
        }


class CommitmentAdmin(ExcelViewMixin, ImportExportModelAdmin):
    """
    Commitment Admin - similar to Expenditure
    """
    resource_class = CommitmentResource
    list_display = ("grant_no", "head", "gross_amount", "date")
    search_fields = ("short_no", "head")
    
    # ✅ Grant fields configuration
    excel_grant_fields = ['seed_grant', 'tdg_grant']

    excel_exclude_fields = ['id', 'short_no', 'seed_grant', 'tdg_grant']
    
    def get_excel_context_data(self):
        return {
            'seed_grants': list(SeedGrant.objects.values('short_no', 'grant_no', 'name')),
            'tdg_grants': list(TDGGrant.objects.values('short_no', 'grant_no', 'name')),
            'heads': json.dumps(HEADS),
        }


# =============================================================================
# Register Models with Custom Admin Site
# =============================================================================
# 💰 Seed Grant Group
custom_admin_site.register(SeedGrant, SeedGrantAdmin)
custom_admin_site.register(TDGGrant, TDGGrantAdmin)
custom_admin_site.register(Expenditure, ExpenditureAdmin)
custom_admin_site.register(Commitment, CommitmentAdmin)

# 📁 Project Master Group
custom_admin_site.register(Project, ProjectAdmin)
custom_admin_site.register(Receipt, ReceiptAdmin)

# 👥 User Management Group
custom_admin_site.register(CustomUser, CustomUserAdmin)
custom_admin_site.register(Faculty)

# admin.py - WORKING VERSION

from .models import FundRequest


class FundRequestAdmin(ExcelViewMixin, admin.ModelAdmin):
    list_display = [
        'faculty_name', 
        'faculty_id',
        'request_date', 
        'project_no', 
        'short_no', 
        'head',
        'amount', 
        'status', 
        'updated_date'
    ]
    
    list_filter = ['status', 'request_date', 'head']
    
    search_fields = [
        'faculty_name', 
        'faculty_id', 
        'project_no', 
        'short_no',
        'project_title'
    ]
    
    
    fieldsets = (
        ('Faculty Information', {
            'fields': ('faculty', 'faculty_name', 'faculty_id')
        }),
        ('Project Details', {
            'fields': (
                'project', 'seed_grant', 'tdg_grant',
                'project_no', 'grant_no', 'project_title', 'short_no'
            )
        }),
        ('Expense Details', {
            'fields': ('head', 'particulars', 'amount')
        }),
        ('Status & Approval', {
            'fields': ('status', 'remarks_by_src', 'request_date', 'updated_date'),
            'classes': ('wide',)
        }),
    )
    
    ordering = ['-request_date']
    
    date_hierarchy = 'request_date'

    excel_exclude_fields = ['id', 'faculty', 'project', 'seed_grant', 'tdg_grant', 'grant_no']
    
    # Make it easier to approve/reject in bulk
    actions = ['approve_requests', 'reject_requests']

    def get_excel_fields_config(self):
        """Override to make specific fields read-only in Excel View"""
        fields = super().get_excel_fields_config()

        editable_fields = ['status', 'remarks_by_src']

        for field in fields:
            if field['name'] not in editable_fields:
                field['editable'] = False
        return fields
    
    def has_add_permission(self, request):
        return False # Disables Add Row Button
    
    def has_delete_permission(self,request, obj=None):
        return False

    
    def approve_requests(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} request(s) approved successfully.')
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} request(s) rejected.')
    reject_requests.short_description = "Reject selected requests"

    def get_excel_context_data(self):
        """
        Provide dropdown options for Excel View
        - Status choices
        - Head options
        """
        return {
            'status_choices': json.dumps(['pending', 'approved', 'rejected']),
            'heads': json.dumps(HEADS),
            'is_fund_request': True,
        }


custom_admin_site.register(FundRequest, FundRequestAdmin)
