from import_export import resources, fields
from .models import Project, Receipt, SeedGrant, TDGGrant, Expenditure, Commitment
from import_export.widgets import DateWidget, ForeignKeyWidget
from datetime import datetime
import xlrd




class FlexibleDateWidget(DateWidget):
    """Universal date parser for Excel + text formats across all imports."""

    def clean(self, value, row=None, *args, **kwargs):
        #  Handle blanks and nulls
        if not value or str(value).strip() in ["", "None", "NULL", "NA", "-", "—"]:
            return None

        #  Excel serial number (int or float)
        try:
            if isinstance(value, (int, float)):
                return datetime(*xlrd.xldate_as_tuple(value, 0)).date()
        except Exception:
            pass

        #  Excel-datetime object (Excel sometimes gives this directly)
        if isinstance(value, datetime):
            return value.date()

        #  Clean text (remove “midnight”, commas, extra spaces)
        value = str(value).replace("midnight", "").replace(",", "").strip()

        # Try multiple possible formats (robust list)
        date_formats = [
            "%d-%b-%Y", "%d/%b/%Y", "%d-%m-%Y", "%d/%m/%Y",
            "%Y-%m-%d", "%b %d %Y", "%b. %d %Y",
            "%d %b %Y", "%d %B %Y", "%B %d %Y"
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        # 🧱 6️⃣ If everything fails — raise clear error
        raise ValueError(f"Invalid date format: {value}")

class ZeroIfBlankWidget:
    """Widget that converts blanks to zero for decimal fields"""
    def clean(self, value, row=None, *args, **kwargs):
        if not value or str(value).strip() in ["", "None", "NULL", "NA", "-"]:
            return 0
        try:
            return float(value)
        except:
            return 0
        
    def render(self, value, obj=None):
        """Convert value back to string during export"""
        if value is None:
            return "0"
        return str(value)





# ✅ Project Resource
class ProjectResource(resources.ModelResource):
    project_no = fields.Field(column_name="Project No.", attribute="project_no")
    project_title = fields.Field(column_name="Project Title", attribute="project_title")
    pi_name = fields.Field(column_name="PI Name", attribute="pi_name")
    faculty_id = fields.Field(column_name="Faculty ID", attribute="faculty_id")
    pi_email = fields.Field(column_name="PI Email ID", attribute="pi_email")
    department = fields.Field(column_name="Department", attribute="department")
    sanction_no = fields.Field(column_name="Sanction No.", attribute="sanction_no")
    sanction_date = fields.Field(column_name="Sanction Date", attribute="sanction_date")
    start_date = fields.Field(column_name="Start Date", attribute="start_date")
    end_date = fields.Field(column_name="End Date", attribute="end_date")

    class Meta:
        model = Project
        import_id_fields = ["project_no"]
        fields = (
            "project_no", "project_title", "pi_name", "pi_email", "faculty_id",
            "department", "sanction_no", "sanction_date",
            "start_date", "end_date"
        )


# ✅ Receipt Resource
class ReceiptResource(resources.ModelResource):
    project = fields.Field(
        column_name="Project No.",
        attribute="project",
        widget=resources.widgets.ForeignKeyWidget(Project, "project_no")
    )
    category = fields.Field(column_name="Category", attribute="category")
    amount = fields.Field(column_name="Sanction Amount", attribute="amount")
    receipt = fields.Field(column_name="Receipt", attribute="receipt")
    payments = fields.Field(column_name="Payments", attribute="payments")
    balance = fields.Field(column_name="Balance", attribute="balance")

    class Meta:
        model = Receipt
        fields = ("project", "category", "amount", "receipt", "payments", "balance")
        export_order = fields


class SeedGrantResource(resources.ModelResource):
    short_no = fields.Field(column_name="Seed grant short no", attribute="short_no")
    grant_no = fields.Field(column_name="Seed Grant no", attribute="grant_no")
    faculty_id = fields.Field(column_name="Faculty ID", attribute="faculty_id")
    name = fields.Field(column_name="Name", attribute="name")
    dept = fields.Field(column_name="Dept", attribute="dept")
    title = fields.Field(column_name="Title", attribute="title")
    sanction_date = fields.Field(column_name="Sanction Date", attribute="sanction_date", widget=FlexibleDateWidget(format="%d-%b-%Y"))
    end_date = fields.Field(column_name="End Date", attribute="end_date", widget=FlexibleDateWidget(format="%d-%b-%Y"))
    budget_year1 = fields.Field(column_name="Budget for 1st Year", attribute="budget_year1")
    budget_year2 = fields.Field(column_name="Budget for 2nd Year", attribute="budget_year2")
    total_budget = fields.Field(column_name="Total", attribute="total_budget")
    equipment = fields.Field(column_name="Equipment", attribute="equipment", widget=ZeroIfBlankWidget() )
    consumables = fields.Field(column_name="Consumabeles", attribute="consumables", widget=ZeroIfBlankWidget())
    contingency = fields.Field(column_name="Contingency", attribute="contingency", widget=ZeroIfBlankWidget())
    travel = fields.Field(column_name="Travel", attribute="travel", widget=ZeroIfBlankWidget())
    manpower = fields.Field(column_name="Manpower", attribute="manpower", widget=ZeroIfBlankWidget())
    others = fields.Field(column_name="Others", attribute="others", widget=ZeroIfBlankWidget())
    furniture = fields.Field(column_name="Furniture", attribute="furniture", widget=ZeroIfBlankWidget())
    visitor_expenses = fields.Field(column_name="Visitor Expenses", attribute="visitor_expenses", widget=ZeroIfBlankWidget())
    lab_equipment = fields.Field(column_name="Lab Equipment", attribute="lab_equipment", widget=ZeroIfBlankWidget())

    class Meta:
        model = SeedGrant
        import_id_fields = ["grant_no"]
        fields =(
            "grant_no", "short_no", "name", "dept", "title", "faculty_id",
            "sanction_date", "end_date", "budget_year1", "budget_year2",
            "total_budget", "equipment", "consumables", "contingency",
            "travel", "manpower", "others", "furniture",
            "visitor_expenses", "lab_equipment"

        )
        export_order = fields


class TDGGrantResource(resources.ModelResource):
    short_no = fields.Field(column_name="Technology Development short no", attribute="short_no")
    grant_no = fields.Field(column_name="Technology Development Grant no", attribute="grant_no")
    faculty_id = fields.Field(column_name="Faculty ID", attribute="faculty_id")
    name = fields.Field(column_name="Name", attribute="name")
    dept = fields.Field(column_name="Dept", attribute="dept")
    title = fields.Field(column_name="Title", attribute="title")
    sanction_date = fields.Field(column_name="Sanction Date", attribute="sanction_date", widget=DateWidget(format="%d-%b-%Y"))
    end_date = fields.Field(column_name="End Date", attribute="end_date", widget=DateWidget(format="%d-%b-%Y"))
    budget_year1 = fields.Field(column_name="Budget for 1st Year", attribute="budget_year1")
    budget_year2 = fields.Field(column_name="Budget for 2nd Year", attribute="budget_year2")
    total = fields.Field(column_name="Total", attribute="total")
    equipment = fields.Field(column_name="Equipment", attribute="equipment")
    consumables = fields.Field(column_name="Consumabeles", attribute="consumables")
    travel = fields.Field(column_name="Travel", attribute="travel")
    manpower = fields.Field(column_name="Manpower", attribute="manpower")
    others = fields.Field(column_name="Others", attribute="others")
    furniture = fields.Field(column_name="Furniture", attribute="furniture")
    visitor_expenses = fields.Field(column_name="Visitor Expenses", attribute="visitor_expenses")
    lab_equipment = fields.Field(column_name="Lab Equipment", attribute="lab_equipment")

    class Meta:
        model = TDGGrant
        import_id_fields = ["grant_no"]
        fields =(
            "grant_no", "short_no", "name", "dept", "title", "faculty_id",
            "sanction_date", "end_date", "budget_year1", "budget_year2",
            "total_budget", "equipment", "consumables", "contingency",
            "travel", "manpower", "others", "furniture",
            "visitor_expenses", "lab_equipment"

        )
        export_order = fields



class ExpenditureResource(resources.ModelResource):
     seed_grant = fields.Field(
        column_name="Seed Grant Short No",
        attribute="seed_grant",
        widget=ForeignKeyWidget(SeedGrant, "short_no")
     )
     tdg_grant = fields.Field(
        column_name="TDG Grant Short No",
        attribute="tdg_grant",
        widget=ForeignKeyWidget(TDGGrant, "short_no")
     )
     date = fields.Field(
        column_name="Date",
        attribute="date",
        widget=FlexibleDateWidget(format="%d-%m-%Y")
     )
     short_no = fields.Field(column_name="Seed grant short no", attribute="short_no")
     grant_no = fields.Field(column_name="Project/Grant No.", attribute="grant_no")
     head = fields.Field(column_name="Expenditure Head", attribute="head")
     particulars = fields.Field(column_name="Particulars", attribute="particulars")
     amount = fields.Field(column_name="Gross Amount (in Rs.)", attribute="amount")
     remarks = fields.Field(column_name="Remarks", attribute="remarks")

     class Meta:
        model = Expenditure
        exclude = ("id",)  # don't include internal ID in Excel
        import_id_fields = []  # let Django auto-create IDs
        fields = (
            "date", "seed_grant", "tdg_grant",
            "short_no", "grant_no", "head",
            "particulars", "amount", "remarks"
        )
        export_order = fields



class CommitmentResource(resources.ModelResource):
    seed_grant = fields.Field(
        column_name="Seed Grant Short No",
        attribute="seed_grant",
        widget=ForeignKeyWidget(SeedGrant, "short_no")
    )
    tdg_grant = fields.Field(
        column_name="TDG Grant Short No",
        attribute="tdg_grant",
        widget=ForeignKeyWidget(TDGGrant, "short_no")
    )
    date = fields.Field(
        column_name="Date",
        attribute="date",
        widget=FlexibleDateWidget(format="%d-%m-%Y")
    )
    short_no = fields.Field(column_name="SDG Short no", attribute="short_no")
    grant_no = fields.Field(column_name="Project/Grant No.", attribute="grant_no")
    head = fields.Field(column_name="Expenditure Head", attribute="head")
    particulars = fields.Field(column_name="Particulars", attribute="particulars")
    gross_amount = fields.Field(column_name="Gross Amount (in Rs.)", attribute="gross_amount")
    remarks = fields.Field(column_name="Remarks", attribute="remarks")

    class Meta:
        model = Commitment
        exclude = ("id",)  # don't include internal ID in Excel
        import_id_fields = []  # let Django auto-create IDs
        fields = (
            "date", "seed_grant", "tdg_grant",
            "short_no", "grant_no", "head",
            "particulars", "gross_amount", "remarks"
        )
        export_order = fields
