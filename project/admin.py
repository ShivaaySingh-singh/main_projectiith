from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.template.response import TemplateResponse
from import_export.admin import ImportExportModelAdmin
from .views import bill_report_admin
from django import forms
from .models import CustomUser, Faculty
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.core.serializers.json import DjangoJSONEncoder

import json  #  ADD THIS - needed for JSON encoding
from .models import models
from .models import (
    Faculty, Project, Receipt, SeedGrant, TDGGrant,
    Expenditure, Commitment, CustomUser, FundRequest, BillInward, TDSSection, TDSRate, Payment, ReceiptHead,ProjectSanctionDistribution,Payee,PaymentType,Bank,CoPiName
)
from .resources import (
    ProjectResource, ReceiptResource, SeedGrantResource,
    TDGGrantResource, ExpenditureResource, CommitmentResource, PaymentResource
)

from .payee_resources import PayeeResource
from .utils import send_async, generate_random_password, send_credentials_email
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

    # for UI - only columns 

    excel_extra_fields = []

    excel_field_order = []
    
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
        context_data['primary_key_field'] = self.get_primary_key_field()
        json_keys = [
            'seed_grants', 'tdg_grants',
            'admin_users', 'tds_sections', 'tds_rates',
            'heads', 'status_choices', 'faculties', 'projects','payees', 'banks','payment_types']
        for k in json_keys:
            if k in context_data:
                val = context_data[k]
            # If it's already a JSON string, keep as-is.
                if isinstance(val, str):
                # try to detect if it's already JSON (starts with [ or {)
                    trimmed = val.strip()
                    if not (trimmed.startswith('[') or trimmed.startswith('{')):
                        context_data[k] = json.dumps(val, cls=DjangoJSONEncoder)
                    else:
                    # keep the string (assume it's already JSON)
                        context_data[k] = val
                else:
                # Python object -> dump to JSON string
                    context_data[k] = json.dumps(val, cls=DjangoJSONEncoder)
            else:
            # ensure key exists as JSON empty array/object where appropriate
                if k in ('heads', 'status_choices', 'faculties', 'admin_users'):
                    context_data[k] = json.dumps([])
                else:
                    context_data[k] = json.dumps([])
        
        
        context = {
            'model_name': model_name.lower(),
            'model_verbose_name': self.model._meta.verbose_name,
            'fields_config': json.dumps(fields_config),
            'enable_grant_selector': len(self.excel_grant_fields) > 0,
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

        fields.extend(getattr(self, "excel_extra_fields", []))

        order = getattr(self, "excel_field_order", [])
        if order:
            field_map = {f["name"]: f for f in fields}

            ordered_fields = []

            for key in order:
                if key in field_map:
                    ordered_fields.append(field_map.pop(key))

            ordered_fields.extend(field_map.values())
            fields = ordered_fields
        
        return fields
    
    def get_primary_key_field(self):
        return 'id'
    
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

        return {
            'seed_grants': json.dumps([]),
             
             
            'tdg_grants': json.dumps([]),
            
            
            'admin_users': json.dumps([]),
            'tds_sections': json.dumps([]),
            'tds_rates': json.dumps([]),
            
            'heads': json.dumps([]),
        }

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
            'Project Master': ['Project', 'Receipt', 'Payment','ProjectSanctionDistribution', 'Payee',],
            'User Management': ['CustomUser', 'Faculty', 'Group'],
            'Fund Request': ['FundRequest'],
            'Inward' : ['BillInward'],
            'TDS' :['TDSSection', 'TDSRate'],
            'Supporting Data': ['ReceiptHead', 'Bank', 'PaymentType','CoPiName'],
           
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

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        required_fields = ['faculty_id', 'pi_name', 'email', 'designation', 'department']
        for field_name in required_fields:
            if field_name in formset.form.base_fields:
                formset.form.base_fields[field_name].required = True
        
        if 'photo' in formset.form.base_fields:
            formset.form.base_fields['photo'].required = False

        return formset 

class FacultyAdmin(admin.ModelAdmin):
    search_fields = (
        "faculty_id",
        "pi_name",
        "department",
    )


class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    inlines = (FacultyInline,)
    #exclude = ("groups", "user_permissions",)  you can uncomment this if you dont want to seee groups and ser permssion

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (("Personal info"), {"fields": ("first_name", "last_name")}),
        (("Role"), {"fields": ("role",)}),
        (("Permissions"), {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",           # ✅ Group assignment
                "user_permissions",  # ✅ Individual permissions
          ),
        }),  
        (("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role"),
        }),
    )
    list_display = ("username", "email", "role", "is_staff", "is_superuser")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    filter_horizontal = ("groups", "user_permissions")

    def get_inline_instances(self, request, obj=None):
        """
        Admin/Sheet role me Faculty inline HIDE 
        Faculty role  me faculty inline SHOW
        """
        inline_instances = []

        if obj is None:
            return super().get_inline_instances(request, obj)
        
        #Existing user edit kar rhe ho  sirf faculty role me inline dikhao 
        if obj.role == 'faculty':
            inline_instances = super().get_inline_instances(request, obj)
        #Admin/sheet role me inline mat dikhao 
        else:
            inline_instances = []

        return inline_instances


    def save_model(self, request, obj, form, change):
        if not change:
            if 'password1' in form.cleaned_data and form.cleaned_data['password1']:
                password = form.cleaned_data['password1']
            else:
                password = generate_random_password()
                obj.set_password(password)

            super().save_model(request, obj, form, change)

            if obj.email:
                send_async(send_credentials_email, obj, password, request)
                
                messages.success(request, f'User "{obj.username}" created successfully. Credentials sent to {obj.email}')
            else:
                messages.warning(request, f'User "{obj.username}" created but no email provided. Password: {password}')   
                    
    def save_formset(self, request, form, formset, change):
        """ Faculty details Validation"""
        instances = formset.save(commit=False)
        user = form.instance

        if user.role == 'faculty':
            if not instances or len(instances) == 0:
                messages.error(request, "faculty role requires all faculty details to be filled!")
                return
            
            faculty = instances[0]
            required_fields = {
                'faculty_id': 'Faculty ID',
                'pi_name': 'PI Name',
                'email': 'Email',
                'designation': 'Designation',
                'department': 'Department'
            }

            missing = []
            for field, label in required_fields.items():
                if not getattr(faculty, field, None):
                    missing.append(label)
            
            if missing:
                messages.error(
                    request, f"Missing required fields: {', '.join(missing)}"
                )
                return
        elif user.role in ['admin', 'sheet']:
            Faculty.objects.filter(user=user).delete()
            messages.info(request, "Faculty details removed (not appliacble for this row)")
            return
        
        for instance in instances:
            instance.save()
        formset.save_m2m()

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
    list_display = ("project_no", "project_title", "project_start_date", "project_end_date", "get_pi_name", "project_status", "sanction_amount",)
    search_fields = ("project_no", "project_title", "faculty__pi_name",)
    readonly_fields = ("project_status","extension_approved_by")
    excel_exclude_fields = []

    excel_extra_fields = [
        {
            "name": "duration",
            "label": "Duration",
            "type": "CharField",
            "editable": False,
            "required": False,
            "width": 150,
        }
    ]

    excel_field_order = [
        "project_short_no",
        "project_no",
        "gender",
        "project_type",
        "faculty",
        "pi_name",
        "co_pi_name",
        "dept",
        "project_title",
        "gst_no",
        "address_sponsoring_agency",
        "pincode",
        "sponsoring_agency",
        "country",
        "project_start_date",
        "project_end_date",
        "duration"
    ]

    def get_pi_name(self, obj):
        if obj.faculty:
            return obj.faculty.pi_name
        return obj.pi
    get_pi_name.short_description = "PI Name"

    def changelist_view(self, request, extra_context=None):
        self._current_request = request
        return super().changelist_view(request, extra_context)

    def get_excel_fields_config(self):
        fields = super().get_excel_fields_config()
        is_superuser = False
        if hasattr(self, "_current_request"):
            is_superuser = self._current_request.user.is_superuser

        for field in fields:
            if field["name"] == "co_pi_name":
                field["dropdown"] = "copis"
                field["valueField"] = "id"
                field["labelField"] = "label"

        for field in fields:
            if field["name"] == "project_status":
                field["editable"] = False

            if field["name"] == "extension_approved_by":
                field["editable"] = False

            if field["name"] == "is_extended":
                field.update({
                    "type": "BooleanField",
                    "editable": is_superuser,
                    "choices": [True, False],
                    "width": 120
                })
            if field["name"] == "extended_end_date":
                field["editable"] = True

            if field["name"] == "extension_reason":
                field["editable"] = True
        return fields

    def get_excel_context_data(self):
        return {
            "faculties": list(
                Faculty.objects.values(
                    "faculty_id", "pi_name", "department"
                )
            ),

            "copis": [
                {
                    "id": c.id,
                    "label": f"{c.name} ({c.faculty_id})"
                }

                for c in CoPiName.objects.all()

            ]
        }
    def save_model(self, request, obj, form, change):
        if obj.is_extended and obj.extension_approved_by is None:
            obj.extension_approved_by = request.user
        super().save_model(request, obj, form, change)

    
    # ✅ No extra configuration needed - Excel View automatically works!


class ReceiptAdmin(ExcelViewMixin, ImportExportModelAdmin):
    resource_class = ReceiptResource
    list_display = ("receipt_date", "project", "head", "amount", "category", "reference_number")

    excel_grant_fields = ['seed_grant', 'tdg_grant', 'project']



    

    excel_exclude_fields = ['id','seed_grant','tdg_grant','project', 'seed_grant_short', 'tdg_grant_short',]

    def get_excel_fields_config(self):
        fields = super().get_excel_fields_config()

        for field in fields:
            if field["name"] == "head":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "dropdown": "heads",
                    "valueField": "id",
                    "labeField": "name",
                    "width": 180,
                })
            return fields
    
    def get_excel_context_data(self):
        return {
            'seed_grants': list(
                SeedGrant.objects.annotate(
                    end_date_str=models.functions.Cast('end_date', models.CharField()),
                    extended_end_date_str=models.functions.Cast('extended_end_date', models.CharField())
                ).values(
                    'id','short_no','grant_no','pi_name',
                    'end_date_str','extended_end_date_str','is_extended','project_status'
                )
            ),

            'tdg_grants': list(
                TDGGrant.objects.annotate(
                    end_date_str=models.functions.Cast('end_date', models.CharField()),
                    extended_end_date_str=models.functions.Cast('extended_end_date', models.CharField())
                ).values(
                    'id','short_no','grant_no','pi_name',
                    'end_date_str','extended_end_date_str','is_extended','project_status'
                )
            ),

            'projects': list(
                Project.objects.annotate(
                    end_date_str=models.functions.Cast('project_end_date', models.CharField()),
                    extended_end_date_str=models.functions.Cast('extended_end_date', models.CharField())
                ).values(
                    'id','project_short_no','project_no','pi_name',
                    'end_date_str','extended_end_date_str','project_status'
                )
            ),

            'heads': list(
                ReceiptHead.objects.values('id','name')
            )
        }


class SeedGrantAdmin(ExcelViewMixin, ImportExportModelAdmin):

    resource_class = SeedGrantResource

    readonly_fields = ("pi_name", "dept")

    

    list_display = ("grant_no", "short_no", "faculty_pi", "faculty_dept", "total_budget", "extension_approved_by_name",)
    search_fields = ("grant_no", "short_no", "faculty__pi_name", "faculty__department")
    excel_exclude_fields = []
    def get_excel_context_data(self):
        return {
            'faculties': list(Faculty.objects.values(
                'faculty_id', 'pi_name', 'department'
            ))
        }
            
    def faculty_pi(self,obj):
        return obj.faculty.pi_name if obj.faculty else "-"
    
    def faculty_dept(self,obj):
        return obj.faculty.department if obj.faculty else "-"
    
    def extension_approved_by_name(self, obj):
        return(
            obj.extension_approved_by.get_full_name()
            or obj.extension_approved_by.username
            if obj.extension_approved_by else "_"
        )
    extension_approved_by_name.short_description = "Approved By"
    

class TDGGrantAdmin(ExcelViewMixin, ImportExportModelAdmin):
    resource_class = TDGGrantResource
    readonly_fields = ("pi_name","dept")
    
    list_display = ("grant_no", "short_no", "faculty_pi", "faculty_dept", "total_budget")
    search_fields = ("grant_no", "short_no", "faculty__pi_name", "faculty__department")
    excel_exclude_fields = []

    def get_excel_context_data(self):
        return {
            'faculties': list(Faculty.objects.values(
                'faculty_id', 'pi_name', 'department'
            ))
        }
    def faculty_pi(self,obj):
        return obj.faculty.pi_name if obj.faculty else "-"
    
    def faculty_dept(self,obj):
        return obj.faculty.department if obj.faculty else "-"
    
    def extension_approved_by_name(self, obj):
        return(
            obj.extension_approved_by.get_full_name()
            or obj.extension_approved_by.username
            if obj.extension_approved_by else "_"
        )
    extension_approved_by_name.short_description = "Approved By"



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
    list_display = ("date","grant_no", "bill_date","head", "amount", )
    search_fields = ("short_no", "head")
    
    # ✅ Tell mixin that this model has grant fields
    excel_grant_fields = ['seed_grant', 'tdg_grant', 'project']
    
    # Hide short numberfrom excel view that is foreign key contains relation
    excel_exclude_fields = ['id', 'short_no', 'seed_grant', 'tdg_grant',  'tdg_grant_short','grant_no_dispaly','seed_grant_short', 'tdg_grant_short']
    
    def get_excel_fields_config(self):
        fields = super().get_excel_fields_config()

        for field in fields:
            if field["name"] == "project":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "dropdown": "projects",
                    "valueField": "id",
                    "labelField": "project_short_no",
                    "width": 220,
                })

        return fields

    def get_excel_context_data(self):
        """
        Provide grant data for dropdowns in Excel view
        JavaScript template will use this data
        """
        return {
            'seed_grants': list(SeedGrant.objects.values('id','short_no', 'grant_no', 'pi_name', 'end_date', 'extended_end_date','project_status')
                                .annotate(
                                    end_date_str = models.functions.Cast('end_date', models.CharField()),
                                    extended_end_date_str= models.functions.Cast('extended_end_date', models.CharField())
                                )
                                .values(
                                    'id','short_no', 'grant_no', 'pi_name', 'end_date_str', 'extended_end_date_str', 'is_extended', 'project_status'
                                )
                            ),
                            
            'tdg_grants': list(TDGGrant.objects.values('id','short_no', 'grant_no', 'pi_name', 'end_date', 'extended_end_date', 'is_extended', 'project_status')
                               
                               .annotate(
                                   end_date_str = models.functions.Cast('end_date', models.CharField()),
                                   extended_end_date_str = models.functions.Cast('extended_end_date',models.CharField())
                               )
                               .values(
                                   'id','short_no', 'grant_no', 'pi_name', 'end_date_str', 'extended_end_date_str', 'is_extended', 'project_status'
                               )
                            ),

            'projects': list(
                Project.objects.annotate(
                    end_date_str=models.functions.Cast("project_end_date", models.CharField()),
                    extended_end_date_str = models.functions.Cast("extended_end_date", models.CharField())
                ).values(
                    "id",
                    "project_short_no",
                    "project_no",
                    "pi_name",
                    "end_date_str",
                    "extended_end_date_str",
                    "project_status",
                )
            ),
                            

            'heads': HEADS,  # Convert list to JSON string
        }


class CommitmentAdmin(ExcelViewMixin, ImportExportModelAdmin):
    """
    Commitment Admin - similar to Expenditure
    """




    resource_class = CommitmentResource
    list_display = ("grant_no", "head", "gross_amount", "date")
    search_fields = ("short_no", "head")
    
    # ✅ Grant fields configuration
    excel_grant_fields = ['seed_grant', 'tdg_grant','project']

    excel_exclude_fields = ['id', 'short_no', 'seed_grant', 'tdg_grant', 'seed_grant_short', 'tdg_grant_short', 'grant_no_display' ]
    
    def get_excel_context_data(self):
        return {
            'seed_grants': list(SeedGrant.objects.values('id','short_no', 'grant_no', 'pi_name', 'end_date', 'extended_end_date', 'project_status')
                                .annotate(
                                    end_date_str = models.functions.Cast('end_date', models.CharField()),
                                    extended_end_date_str = models.functions.Cast('extended_end_date', models.CharField())
                                )
                                .values(
                                    'id','short_no', 'grant_no', 'pi_name', 'end_date_str', 'extended_end_date_str', 'is_extended', 'project_status'
                                )
                            ),
            'tdg_grants': list(TDGGrant.objects.values('id','short_no', 'grant_no', 'pi_name', 'end_date', 'extended_end_date', 'is_extended', 'project_status')
                               .annotate(
                                   end_date_str = models.functions.Cast('end_date',models.CharField()),
                                   extended_end_date_str = models.functions.Cast('extended_end_date', models.CharField())
                               )
                               .values(
                                   'id','short_no', 'grant_no', 'pi_name', 'end_date_str', 'is_extended', 'project_status', 'extended_end_date_str'
                               )
                            ),
            'projects': list(
                Project.objects.annotate(
                    end_date_str=models.functions.Cast("project_end_date", models.CharField()),
                    extended_end_date_str = models.functions.Cast("extended_end_date", models.CharField())
                ).values(
                    "id",
                    "project_short_no",
                    "project_no",
                    "pi_name",
                    "end_date_str",
                    "extended_end_date_str",
                    "project_status",
                )
            ),
            'heads': json.dumps(HEADS),
        }

class BillInwardAdmin(ExcelViewMixin,admin.ModelAdmin):
    list_display = ['date','pi_name','get_faculty_id','project_no','amount','tds_section','tds_rate','tds_amount','net_amount','under_head','get_assigned_to','status_badge','outward_date','bill_pdf_link']

    list_filter = ['bill_status', 'date', 'whom_to', 'under_head','faculty']
    readonly_fields = ('bill_pdf_link',)
    search_fields = [
        'pi_name',
        'faculty__pi_name',
        'faculty__faculty_id',
        'project_no',
        'received_from',
        'particulars',
        'po_no',
    ]
    date_hierarchy = 'date'

    ordering = ['-date', '-id']

    excel_exclude_fields = ['id']
    
    # PDF Link
    def bill_pdf_link(self, obj):
        if obj.bill_pdf:
            return format_html('<a href="{}" target="_blank">View PDF</a>', obj.bill_pdf.url)
        return "No File"
    bill_pdf_link.short_description = "Bill PDF"


    def get_faculty_id(self, obj):
        return obj.faculty.faculty_id if obj.faculty else "_"
    get_faculty_id.short_description = "Faculty ID"

    def faculty_name(self,obj):
        return obj.faculty.pi_name if obj.faculty else "-"
    

    def get_assigned_to(self, obj):
        """Display assigned admin member name"""
        if obj.whom_to:
            full_name = obj.whom_to.get_full_name()
            return full_name if full_name else obj.whom_to.username
        return "-"
    get_assigned_to.short_description = "Assigned To"
    

    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'pending': '#ff9800',    # Orange
            'processed': '#4caf50',  # Green
            'returned': '#f44336',   # Red
        }
        color = colors.get(obj.bill_status, '#999')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:3px; font-size:11px; font-weight:500;">{}</span>',
            color,
            obj.get_bill_status_display()
        )
    status_badge.short_description = "Status"
    

    def get_queryset(self, request):
        """
        Filter bills based on user role:
        - Superuser: See all bills
        - Admin Member: See only assigned bills
        - Others: No access
        """
        qs = super().get_queryset(request)
        qs = qs.select_related('faculty', 'whom_to')
        
        if request.user.is_superuser:
            return qs
        elif request.user.groups.filter(name="billinward").exists():
            return qs
        elif hasattr(request.user, 'role') and request.user.role == 'admin':
            return qs.filter(whom_to=request.user)
        else:
            return qs.none()
        
    def has_add_permission(self, request):
        """Only superusers can add bills via Excel View"""
        return (
            request.user.is_superuser or
            request.user.groups.filter(name="billinward").exists()
        )
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete bills"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Both superusers and admin members can change bills"""
        if request.user.is_superuser:
            return True
        if request.user.groups.filter(name="billinward").exists():
            return True
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            if obj is None:
                return True
            return obj.whom_to == request.user
            
        return False
    
    def has_view_permission(self, request, obj=None):
        """Both superusers and admin members can view bills"""
        return self.has_change_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        ro = set(self.readonly_fields)

        if (
            request.user.is_superuser or 
            request.user.groups.filter(name="billinward").exists()
        ):
            return list(ro)
        
        if hasattr(request.user, 'role') and request.user.role =='admin':
            ro.add('bill_pdf')

        return list(ro)
    
    def get_excel_fields_config(self):
        """
        Configure Excel View fields with role-based editability
        
        Superuser: All fields editable
        Admin Member: Only status, outward_date, remarks editable
        
        ✅ Faculty ID → User enters, Name auto-fills from FK
        ✅ If Faculty ID not found, user can manually enter Faculty Name
        """
        request = getattr(self, '_current_request', None)
        
        # Base field configuration
        fields_config = [
            {
                'name': 'date',
                'label': 'Date',
                'type': 'DateField',
                'editable': True,
                'required': True,
                'width': 130
            },
            {
                'name': 'received_from',
                'label': 'Received From',
                'type': 'CharField',
                'editable': True,
                'required': False,
                'width': 180
            },
            {
                'name': 'faculty',
                'label': 'Faculty ID',
                'type': 'ForeignKey',
                'editable': True,
                'required': False,  # Optional - can enter manually
                'width': 180,
                'help_text': 'Select Faculty ID - Name will auto-fill'
            },
            {
                'name': 'pi_name',
                'label': 'PI Name',
                'type': 'CharField',
                'editable': True,  # ✅ Changed to True - manual entry allowed
                'required': False,
                'width': 220,
                'help_text': 'Auto-fills from Faculty ID, or enter manually'
            },
            {
                'name': 'project_no',
                'label': 'Project No.',
                'type': 'CharField',
                'editable': True,
                'required': False,
                'width': 150
            },
            {
                'name': 'particulars',
                'label': 'Particulars',
                'type': 'TextField',
                'editable': True,
                'required': False,
                'width': 300
            },
            {
                'name': 'amount',
                'label': 'Amount (₹)',
                'type': 'DecimalField',
                'editable': True,
                'required': True,
                'width': 150
            },
            {
                'name': 'tds_section',
                'label': 'TDS_Section',
                'type': 'ForeignKey',
                'editable': True,
                'required': True,
                'width':120
            },
           {
                'name': 'tds_rate',
                'label': 'TDs_Rate',
                'type': 'ForeignKey',
                'editable': True ,
                'required': True,
                'width': 120
            },   
              
            {
                'name': 'tds_amount',
                'label': 'TDS Amount',
                'type': 'DecimalField',
                'editable': False,
                'required': False,
                'width': 150
            },
            {
                'name': 'net_amount',
                'label': 'Net Amount',
                'type': 'DecimalField',
                'editable': False,
                'required': False,
                'width': 150
            },
            {
                'name': 'under_head',
                'label': 'Under Head',
                'type': 'CharField',
                'editable': True,
                'required': False,
                'width': 180
            },
            {
                'name': 'po_no',
                'label': 'PO No.',
                'type': 'CharField',
                'editable': True,
                'required': False,
                'width': 150
            },
            {
                'name': 'whom_to',
                'label': 'Assigned To',
                'type': 'ForeignKey',
                'editable': True,
                'required': False,
                'width': 200
            },
            {
                'name': 'bill_status',
                'label': 'Status',
                'type': 'CharField',
                'editable': True,
                'required': True,
                'width': 150,
                'choices': ['pending', 'processed', 'returned']
            },
            {
                'name': 'outward_date',
                'label': 'Outward Date',
                'type': 'DateField',
                'editable': True,
                'required': False,
                'width': 130
            },
            {
                'name': 'remarks',
                'label': 'Remarks',
                'type': 'TextField',
                'editable': True,
                'required': False,
                'width': 300
            },
        ]
        
        # Apply role-based restrictions
        if request and not (
            request.user.is_superuser or
            request.user.groups.filter(name="billinward").exists()
        ):
            if hasattr(request.user, 'role') and request.user.role == 'admin':
                # Admin members can only edit these fields
                editable_fields = ['tds_section', 'tds_rate','bill_status', 'outward_date', 'remarks']
                
                for field in fields_config:
                    if field['name'] not in editable_fields:
                        field['editable'] = False
        
        return fields_config
    
    # ========================================================================
    # Excel View Context Data (Dropdowns & Options)
    # ========================================================================
    
    def get_excel_context_data(self):
        """
        Provide dropdown options for Excel View:
        - Status choices
        - Faculty list
        - Admin users list (superuser only)
        """
        request = getattr(self, '_current_request', None)

        
        
        context = {
            'status_choices': json.dumps([
                {'value': 'pending', 'label': 'Pending'},
                {'value': 'processed', 'label': 'Processed'},
                {'value': 'returned', 'label': 'Returned'},
            ]),
            'faculties': json.dumps([
                {
                    'faculty_id': f.faculty_id,
                    'pi_name': f'{f.pi_name} ({f.faculty_id})',
                    
                }
                for f in Faculty.objects.all().order_by('pi_name')
            ]),
        }

        context['tds_sections'] = json.dumps([
            {'id': s.id, 'code':s.section}
            for s in TDSSection.objects.all().order_by('section')
        ])

        context['tds_rates'] = json.dumps([
            {'id': r.id, 'section_id': r.section_id, 'percent': float(r.percent)}
            for r in TDSRate.objects.select_related("section").all()

            
        ])
        
        # Only superuser can see admin users for assignment
        if request and (request.user.is_superuser or request.user.groups.filter(name="billinward").exists()):
            admin_users = CustomUser.objects.filter(
                Q(role='admin') | Q(is_staff=True)
            ).order_by('first_name', 'last_name')
            
            context['admin_users'] = json.dumps([
                {
                    'id': u.id,
                    'name': f'{u.get_full_name() or u.username} '
                }
                for u in admin_users
            ])
        else:
            context['admin_users'] = json.dumps([])
        
        return context
    
    # ========================================================================
    # Excel View Override (Store request for context)
    # ========================================================================
    
    def excel_view(self, request):
        """Store request object for use in field config and context"""
        self._current_request = request
        return super().excel_view(request)
    
    # ========================================================================
    # Save Model (Auto-set created_by)
    # ========================================================================
    
    def save_model(self, request, obj, form, change):
        """
        Auto-populate fields on save
        
         created_by: Auto-set to logged-in user (new bills only)
         faculty_name: Auto-fill from Faculty FK if selected
         If no Faculty FK but faculty_name provided: Save as manual entry
        """
        if not change:  # New object
            obj.created_by = request.user
        
        # Auto-populate faculty_name from Faculty FK if selected
        if obj.faculty:
            obj.pi_name = obj.faculty.pi_name
        # If faculty_name is manually entered, keep it as is
        # (no change needed, it's already set by user)
        if obj.tds_rate and obj.amount:
            obj.tds_amount = (obj.amount * obj.tds_rate.percent) / 100
            obj.net_amount = obj.amount -obj.tds_amount
        else:
            obj.tds_amount = 0
            obj.net_amount = obj.amount
        
        super().save_model(request, obj, form, change)

class PaymentAdmin(ExcelViewMixin, ImportExportModelAdmin):
    resource_class = PaymentResource

    list_display = ("date","head","payment_type","payee","utr_no","net_amount","project")

    list_filter = ("payment_type",
        "head",
        
        "gst_tds_type",
        "tds_section",
        "tds_rate",
        "date",

    )
    search_fields = (
        
        "payee__name_of_payee",
        "utr_no",
        "payee_account_no",
        "payee_ifsc",
    )

    excel_grant_fields = ["seed_grant", "tdg_grant", "project"]
    excel_exclude_fields = ["id", "seed_grant", "tdg_grant","project",'seed_grant_short', 'tdg_grant_short',]
    def get_excel_fields_config(self):
        fields = super().get_excel_fields_config()


        for field in fields:
            
            if field["name"] =="project":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    
                    "dropdown": "projects",
                    "valueField": "id",
                    
                    "width": 220,
                    
                    "labelField": "project_short_no",
                    
                })

            if field["name"] == "seed_grant":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "dropdown": "seed_grants",
                    "valueField": "id",
                    "labelField": "short_no",
                    "width": 200,
                })

            if field["name"] == "tdg_grant":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "dropdown": "tdg_grants",
                    "valueField": "id",
                    "labelField": "short_no",
                    "width": 200,
                })
                
            
            if field["name"] == "head":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "width": 180,

                    "dropdown": "heads",

                    "valueField": "id",
                    "labelField": "name",
                })

            if field["name"] == "bank":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "dropdown": "banks",
                    "valueField": "id",
                    "labelField": "short_no",
                    "width": 180,

                })

            if field["name"] == "payment_type":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "dropdown": "payment_types",
                    "valueField": "id",
                    "labelField": "name",
                    "width": 180,
                })
            if field["name"] == "payee":
                field.update({
                    "editable": False,
                    "width": 250,
                })

            if field["name"] == "payee_pan":
                field.update({
                    "type": "CharField",
                    "editable": True,
                    "dropdown": "payees",
                    "valueField":"id",
                    "labelField": "pan",
                    "width": 200,
                })

            if field["name"] in [
                "payee_bank_name",
                "payee_branch_name",
                "payee_account_no",
                "payee_ifsc",
                
                "payee_email",
                "tds_amount",
                "net_amount",

            ]:
                field["editable"] = False   

            
        return fields
    
    def get_excel_context_data(self):
        return {
            "projects": list(
                Project.objects.annotate(
                    end_date_str=models.functions.Cast(
                        "project_end_date", models.CharField()
                    ),
                    extended_end_date_str=models.functions.Cast(
                        "extended_end_date", models.CharField()
                    ),
                ).values(
                    "id",
                    "project_short_no",
                    "project_no",
                    "pi_name",
                    "end_date_str",
                    "extended_end_date_str",
                    "project_status",
                )
            ),

            "seed_grants": list(
                SeedGrant.objects.annotate(
                    end_date_str=models.functions.Cast("end_date", models.CharField()),
                    extended_end_date_str=models.functions.Cast(
                        "extended_end_date", models.CharField()
                    ),
                ).values(
                    "id",
                    "short_no",
                    "grant_no",
                    "pi_name",
                    "end_date_str",
                    "extended_end_date_str",
                    "project_status",
                )
            ),

            "tdg_grants": list(
                TDGGrant.objects.annotate(
                    end_date_str=models.functions.Cast("end_date", models.CharField()),
                    extended_end_date_str=models.functions.Cast(
                        "extended_end_date", models.CharField()
                    ),
                ).values(
                    "id",
                    "short_no",
                    "grant_no",
                    "pi_name",
                    "end_date_str",
                    "extended_end_date_str",
                    "project_status",
                )
            ),

            "heads": list(
                ReceiptHead.objects.values("id", "name").order_by("name")
            ),

            "payment_types": list(
                PaymentType.objects.values("id", "name").order_by("name")
            ),

            "banks": list(
                Bank.objects.filter(is_active=True)
                .values("id", "short_no", "bank_name")
                .order_by("short_no")
            ),

            "payees": list(
                Payee.objects.values(
                    "id",
                    "name_of_payee",
                    "bank_name",
                    "branch",
                    "account_number",
                    "ifsc",
                    "pan",
                    "email",
                ).order_by("name_of_payee")
            ),

            "tds_sections": list(
                TDSSection.objects.values("id", "section").order_by("section")
            ),

            "tds_rates": list(
                TDSRate.objects.values("id", "section_id", "percent")
            ),
        }

    # ==========================================================
    # Auto Calculations on Save
    # ==========================================================
    def save_model(self, request, obj, form, change):
        # Auto PI info from funding
        funding = obj.project or obj.seed_grant or obj.tdg_grant
        if funding:
            obj.pi_name = getattr(funding, "pi_name", None)
            faculty = getattr(funding, "faculty", None)
            obj.pi_email = faculty.email if faculty else None

        # Auto-fill payee snapshot
        if obj.payee:
            obj.payee_account_no = obj.payee.account_number
            obj.payee_bank_name = obj.payee.bank_name
            obj.payee_branch_name = obj.payee.branch
            obj.payee_ifsc = obj.payee.ifsc
            obj.payee_email = obj.payee.email
            obj.payee_pan = obj.payee.pan

        # Auto TDS calculation
        if obj.tds_rate and obj.amount:
            obj.tds_amount = (obj.amount * obj.tds_rate.percent) / 100
            obj.net_amount = obj.amount - obj.tds_amount
        else:
            obj.tds_amount = 0
            obj.net_amount = obj.amount

        super().save_model(request, obj, form, change)


    

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
custom_admin_site.register(BillInward, BillInwardAdmin)
custom_admin_site.register(Payment, PaymentAdmin)



# 👥 User Management Group
custom_admin_site.register(CustomUser, CustomUserAdmin)
custom_admin_site.register(Faculty, FacultyAdmin)
custom_admin_site.register(Group)

# admin.py - WORKING VERSION

from .models import FundRequest


class FundRequestAdmin(ExcelViewMixin, admin.ModelAdmin):
    list_display = [
        'pi_name', 
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
        'pi_name', 
        'faculty_id', 
        'project_no', 
        'short_no',
        'project_title'
    ]
    
    
    fieldsets = (
        ('Faculty Information', {
            'fields': ('faculty', 'pi_name', 'faculty_id')
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

class TDSSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "section")
    search_fields = ("Section",)

class TDSRateAdmin(admin.ModelAdmin):
    list_display = ("id", "section", "percent")
    list_filter = ("section",)
    search_fields = ("section__section",)

class ReceiptHeadAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    list_filter = ("name",)
    search_fields = ("name",)

class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

class CoPiNameAdmin(admin.ModelAdmin):
    list_display = ("faculty_id", "name")
    search_fields = ("name",)
    
class BankAdmin(admin.ModelAdmin):
    list_display = (
        "bank_name",
        "short_no",
        "account_no",
        "scheme_code",
        "is_active"
    )
    search_fields = (
        "bank_name", 
        "short_no"
    )

    list_filter = ("is_active",)


custom_admin_site.register(TDSSection, TDSSectionAdmin)
custom_admin_site.register(TDSRate, TDSRateAdmin)
custom_admin_site.register(ReceiptHead, ReceiptHeadAdmin)
custom_admin_site.register(PaymentType, PaymentTypeAdmin)
custom_admin_site.register(Bank, BankAdmin)
custom_admin_site.register(CoPiName, CoPiNameAdmin)


    
class ProjectSanctionDistributionAdmin(ExcelViewMixin, admin.ModelAdmin):
    list_display = ("project","financial_year", "project_year", "head", "sanctioned_amount")
    list_filter = ("financial_year", "project_year", "head")


    search_fields = ("project__project_no", "project__project_short_no")

    
    
    excel_exclude_fields = [
        "id",
        
    ]

    

    

    def get_excel_fields_config(self):
        fields = super().get_excel_fields_config()

        for field in fields:
            if field["name"] == "project":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "dropdown": "projects",
                    "valueField": "id",
                    "labelField": "project_short_no",
                    "width": 200,
                })

            


            if field["name"] == "head":
                field.update({
                    "type": "ForeignKey",
                    "editable": True,
                    "dropdown": "heads",
                    "valueField": "id",
                    "labelField": "name",
                    "width": 180,
                })
        return fields
    
    def get_excel_context_data(self):
        return {

            
            "projects": list(
                Project.objects.values(
                    "id",
                    "project_short_no",
                    "project_no",
                    
                ).order_by("project_short_no") 
                
            ),

          

        
            "heads": list(
                ReceiptHead.objects.values(
                    "id",
                    "name",
                ).order_by("name")
            ),
        }
    
    

custom_admin_site.register(ProjectSanctionDistribution, ProjectSanctionDistributionAdmin)

          
class PayeeAdmin(ExcelViewMixin, admin.ModelAdmin):
    resource_class = PayeeResource
    list_diplay = (
        "name_of_payee",
        "payee_type",
        "bank_name",
        "account_number",
        "email",
        
    )
    search_fields = (
        "name_of_payee",
        "emp_code",
        "pan",
        "gst",
        "pfms_code",
        "email",

    )
    list_filter = ("payee_type", )

custom_admin_site.register(Payee, PayeeAdmin)

