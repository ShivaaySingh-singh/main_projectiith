from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.template.response import TemplateResponse
from import_export.admin import ImportExportModelAdmin
from .views import bill_report_admin
from django import forms
from .models import CustomUser, Faculty

from .models import (
    Faculty, Project, Receipt, SeedGrant, TDGGrant,
    Expenditure, Commitment, CustomUser
)
from .resources import (
    ProjectResource, ReceiptResource, SeedGrantResource,
    TDGGrantResource, ExpenditureResource, CommitmentResource
)

from .utils import generate_random_password, send_credentials_email
from django.contrib import messages


# =====================
# Custom Admin Site with Grouping
# =====================
class CustomAdminSite(admin.AdminSite):
    site_header = "IIT Hyderabad (SRC) - Admin Panel"
    site_title = "IIT Hyderabad SRC Admin"
    index_title = "Welcome to SRC Admin Dashboard"

    def get_app_list(self, request, app_label=None):
        """
        Custom grouping for admin sidebar
        """
        # Define custom groups with models 
        custom_groups = {
            'Seed Grant': ['SeedGrant', 'TDGGrant', 'Expenditure', 'Commitment'],
            'Project Master': ['Project', 'Receipt'],
            'User Management': ['CustomUser', 'Faculty'],
        }

        # Build default app directory
        app_dict = self._build_app_dict(request, app_label)

        # Reorganize into custom groups
        custom_app_list = []

        for group_name, model_names in custom_groups.items():
            group_models = []

            # Collect models for this group
            for app_name, app_data in app_dict.items():
                for model in app_data['models']:
                    if model['object_name'] in model_names:
                        group_models.append(model)
                        
            # Add group if it has models
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


# Custom Views ko class ke baad define karo
def project_fund_detail_view(request):
    return TemplateResponse(request, "admin/fund_management.html", {})


def seed_grant_detail_view(request):
    return bill_report_admin(request)


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')


# =====================
# Custom User Creation Form
# =====================
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
        """Auto-generate username from email if not provided"""
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
        """Validate passwords match (only if provided)"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if not password1 and not password2:
            return password2
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return password2

    def save(self, commit=True):
        """Save user with password handling"""
        user = super().save(commit=False)
        
        password = self.cleaned_data.get("password1")
        
        if not password:
            password = generate_random_password()
        
        user.set_password(password)
        
        if commit:
            user.save()
        
        user._temp_password = password
        
        return user


# =====================
# Faculty inline in User
# =====================
class FacultyInline(admin.StackedInline):
    model = Faculty
    can_delete = False
    verbose_name_plural = "Faculty Details"
    fk_name = "user"
    extra = 0


# =====================
# Custom User Admin
# =====================
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
        """Override to send credentials email when creating new user"""
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
                    messages.success(
                        request,
                        f'User "{obj.username}" created successfully. '
                        f'Credentials sent to {obj.email}'
                    )
                else:
                    messages.warning(
                        request,
                        f'User "{obj.username}" created but email failed to send. '
                        f'Password: {password}'
                    )
            else:
                messages.warning(
                    request,
                    f'User "{obj.username}" created but no email provided. '
                    f'Password: {password}'
                )
        else:
            super().save_model(request, obj, form, change)


# =====================
# Other Model Admins
# =====================
class ProjectAdmin(ImportExportModelAdmin):
    resource_class = ProjectResource
    list_display = ("project_no", "project_title", "start_date", "end_date", "pi_name")
    search_fields = ("project_no", "project_title", "pi_name")


class ReceiptAdmin(ImportExportModelAdmin):
    resource_class = ReceiptResource
    list_display = ("project", "category", "amount", "equipment", "manpower", "consumables")
    search_fields = ("project__project_no", "category")


class SeedGrantAdmin(ImportExportModelAdmin):
    resource_class = SeedGrantResource
    list_display = ("grant_no", "short_no", "name", "dept", "total_budget")
    search_fields = ("grant_no", "short_no", "name")


class TDGGrantAdmin(ImportExportModelAdmin):
    resource_class = TDGGrantResource
    list_display = ("grant_no", "short_no", "name", "dept", "total_budget")
    search_fields = ("grant_no", "short_no", "name")


class ExpenditureAdmin(ImportExportModelAdmin):
    resource_class = ExpenditureResource
    list_display = ("grant_no", "head", "amount", "date")
    search_fields = ("short_no", "head")


class CommitmentAdmin(ImportExportModelAdmin):
    resource_class = CommitmentResource
    list_display = ("grant_no", "head", "gross_amount", "date")
    search_fields = ("short_no", "head")


# =====================
# Register Models with Custom Admin Site
# =====================
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