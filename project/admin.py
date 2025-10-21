from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.template.response import TemplateResponse
from import_export.admin import ImportExportModelAdmin
from .views import bill_report_admin

from .models import (
    Faculty, Project, Receipt, SeedGrant, TDGGrant,
    Expenditure, Commitment, CustomUser
)
from .resources import (
    ProjectResource, ReceiptResource, SeedGrantResource,
    TDGGrantResource, ExpenditureResource, CommitmentResource
)



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


class TDGGrantAdmin(ImportExportModelAdmin):
    resource_class = TDGGrantResource
    list_display = ("grant_no", "short_no", "name", "dept", "total_budget")


class ExpenditureAdmin(ImportExportModelAdmin):
    resource_class = ExpenditureResource
    list_display = ("grant_no", "head", "amount", "date")


class CommitmentAdmin(ImportExportModelAdmin):
    resource_class = CommitmentResource
    list_display = ("grant_no", "head", "gross_amount", "date")


# =====================
# Inject Custom Pages in Default Admin
# =====================
def project_fund_detail_view(request):
    return TemplateResponse(request, "admin/fund_management.html", {})

def seed_grant_detail_view(request):
    return bill_report_admin(request)



original_get_urls = admin.site.get_urls


# Add custom URLs (buttons) to the default admin
def get_custom_admin_urls():
    urls = original_get_urls()

    custom_urls = [
        path("project-fund-detail/", admin.site.admin_view(project_fund_detail_view), name="project_fund_detail"),
        path("seed-grant-detail/", admin.site.admin_view(seed_grant_detail_view), name="seed_grant_detail"),
    ]
    return custom_urls + urls

admin.site.get_urls = get_custom_admin_urls


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Faculty)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(SeedGrant, SeedGrantAdmin)
admin.site.register(TDGGrant, TDGGrantAdmin)
admin.site.register(Expenditure, ExpenditureAdmin)
admin.site.register(Commitment, CommitmentAdmin)