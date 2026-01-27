from import_export import resources
from .models import Payee

class PayeeResource(resources.ModelResource):
    class Meta:
        model = Payee
        import_id_fields = ("id",)
        fields = (
            "id", "payee_type", "name_of_payee", "emp_code", "designation",
            "department",
            "pan",
            "gst",
            "account_number",
            "bank_name",
            "branch",
            "ifsc",
            "email",
            "contact_no",
            "pfms_code",
            "pfms_name",
            "is_active",
        )
