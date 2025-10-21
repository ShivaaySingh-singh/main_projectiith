# sheets_portal/admin.py
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import GoogleSheet

class GoogleSheetResource(resources.ModelResource):
    class Meta:
        model = GoogleSheet
        fields = ('id', 'title', 'sheet_url')   # include 'id' is helpful but optional

@admin.register(GoogleSheet)
class GoogleSheetAdmin(ImportExportModelAdmin):   # <-- Use ImportExportModelAdmin
    resource_class = GoogleSheetResource
    list_display = ('title', 'sheet_url')

