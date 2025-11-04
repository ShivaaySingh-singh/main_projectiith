from import_export import resources, fields
from .models import Project, Receipt, SeedGrant, TDGGrant, Expenditure, Commitment
from import_export.widgets import DateWidget, ForeignKeyWidget
from datetime import datetime, date
import xlrd




class FlexibleDateWidget(DateWidget):
    """Universal date parser for Excel + text formats across all imports."""

    def clean(self, value, row=None, *args, **kwargs):
        # 1️⃣ Handle empty or invalid placeholders
        if not value or str(value).strip() in ["", "None", "NULL", "NA", "-", "—"]:
            return None

        # 2️⃣ Handle Excel serial numbers (numeric dates)
        if isinstance(value, (int, float)):
            for datemode in (0, 1):  # Windows and Mac
                try:
                    return datetime(*xlrd.xldate_as_tuple(value, datemode)).date()
                except Exception:
                    continue

        # 3️⃣ Handle datetime/date objects directly
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value

        # 4️⃣ Clean up text value
        value = str(value).strip()
        value = (
            value.replace("–", "-")
                 .replace("—", "-")
                 .replace(",", "")
                 .replace(".", "-")  # handle 1.1.2025
        )

        # 5️⃣ Try common formats
        date_formats = [
            "%d-%b-%Y",  # 01-Jan-2025
            "%d-%B-%Y",  # 01-January-2025
            "%d-%m-%Y",  # 01-01-2025
            "%Y-%m-%d",  # 2025-01-01
            "%d/%m/%Y",  # 01/01/2025
            "%m/%d/%Y",  # US format
            "%d-%b-%y",  # 01-Jan-25
            "%d-%m-%y",  # 01-01-25
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        # 6️⃣ Last fallback - auto parser
        try:
            from dateutil import parser
            return parser.parse(value, dayfirst=True).date()
        except Exception:
            pass

        
        raise ValueError(f"Invalid date format: '{value}' (rpw:{row})")
    
    def render(self, value, obj=None):
        if value:
            return value.strftime("%d-%b-%Y")
        return ""


       

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
    sanction_date = fields.Field(column_name="Sanction Date", attribute="sanction_date", widget=FlexibleDateWidget())
    start_date = fields.Field(column_name="Start Date", attribute="start_date", widget=FlexibleDateWidget())
    end_date = fields.Field(column_name="End Date", attribute="end_date", widget=FlexibleDateWidget())

    class Meta:
        model = Project
        import_id_fields = ["project_no"]
        skip_unchnaged = True
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
    sanction_date = fields.Field(column_name="Sanction Date", attribute="sanction_date", widget=FlexibleDateWidget())
    end_date = fields.Field(column_name="End Date", attribute="end_date", widget=FlexibleDateWidget())
    budget_year1 = fields.Field(column_name="Budget for 1st Year", attribute="budget_year1",widget=ZeroIfBlankWidget())
    budget_year2 = fields.Field(column_name="Budget for 2nd Year", attribute="budget_year2", widget=ZeroIfBlankWidget())
    total_budget = fields.Field(column_name="Total", attribute="total_budget")
    equipment = fields.Field(column_name="Equipment", attribute="equipment", widget=ZeroIfBlankWidget() )
    consumables = fields.Field(column_name="Consumables", attribute="consumables", widget=ZeroIfBlankWidget())
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
        skip_unchanged = True
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
    sanction_date = fields.Field(column_name="Sanction Date", attribute="sanction_date", widget=FlexibleDateWidget())
    end_date = fields.Field(column_name="End Date", attribute="end_date", widget=FlexibleDateWidget())
    budget_year1 = fields.Field(column_name="Budget for 1st Year", attribute="budget_year1", widget=ZeroIfBlankWidget())
    budget_year2 = fields.Field(column_name="Budget for 2nd Year", attribute="budget_year2", widget=ZeroIfBlankWidget())
    total_budget = fields.Field(column_name="Total", attribute="total_budget")
    equipment = fields.Field(column_name="Equipment", attribute="equipment", widget=ZeroIfBlankWidget())
    consumables = fields.Field(column_name="Consumabeles", attribute="consumables", widget=ZeroIfBlankWidget())
    travel = fields.Field(column_name="Travel", attribute="travel", widget=ZeroIfBlankWidget())
    manpower = fields.Field(column_name="Manpower", attribute="manpower", widget=ZeroIfBlankWidget())
    others = fields.Field(column_name="Others", attribute="others",widget=ZeroIfBlankWidget())
    furniture = fields.Field(column_name="Furniture", attribute="furniture", widget=ZeroIfBlankWidget())
    visitor_expenses = fields.Field(column_name="Visitor Expenses", attribute="visitor_expenses", widget=ZeroIfBlankWidget())
    lab_equipment = fields.Field(column_name="Lab Equipment", attribute="lab_equipment", widget=ZeroIfBlankWidget())

    class Meta:
        model = TDGGrant
        import_id_fields = ["grant_no"]
        skip_unchanged = True
        fields =(
            "grant_no", "short_no", "name", "dept", "title", "faculty_id",
            "sanction_date", "end_date", "budget_year1", "budget_year2",
            "total_budget", "equipment", "consumables", "contingency",
            "travel", "manpower", "others", "furniture",
            "visitor_expenses", "lab_equipment"

        )
        export_order = fields



class ExpenditureResource(resources.ModelResource):
     grant_short_no =fields.Field(
         column_name="Grant Short No",
         attribute="grant_short_no"
     )
     date = fields.Field(
        column_name="Date",
        attribute="date",
        widget=FlexibleDateWidget()
     )
     
     # Explicitly define Foreignkey fields with widget
     seed_grant = fields.Field(
         attribute='seed_grant',
         widget=ForeignKeyWidget(SeedGrant, field='short_no')
     )

     tdg_grant = fields.Field(
         attribute ='tdg_grant',
         widget = ForeignKeyWidget(SeedGrant, field='short_no')
     )

     head = fields.Field(column_name= "Expenditure Head", attribute="head")
     particulars = fields.Field(column_name="Particulars", attribute="particulars")
     amount = fields.Field(column_name="Gross Amount (in Rs.)", attribute="amount")
     remarks = fields.Field(column_name="Remarks", attribute="remarks")

     grant_no = fields.Field( attribute="grant_no", readonly=True)
     short_no = fields.Field(attribute="short_no", readonly=True)
    
     def before_import_row(self, row, **kwargs):
            short_no_value = str(row.get("Grant Short No", "")).strip()

            if not short_no_value:
                raise ValueError("Grant Short No is requiredbut missing")
            
            
            seed_exists = SeedGrant.objects.filter(short_no=short_no_value).first()
            if seed_exists:
                row["seed_grant"] = short_no_value
                row["tdg_grant"] = None
                return
            
            tdg_exists = TDGGrant.objects.filter(short_no=short_no_value).first()
            if tdg_exists:
                row["tdg_grant"] = short_no_value
                row["seed_grant"] = None
                return
           
            

            raise ValueError(f"Grant with Short_no '{short_no_value}' not found in Seed or TDG")
     
     class Meta:
        model = Expenditure
        exclude = ("id",)  # don't include internal ID in Excel
        import_id_fields = []  # let Django auto-create IDs
        skip_unchanged = True
        fields = (
            "date", "seed_grant", "tdg_grant",
            "short_no", "grant_no", "head",
            "particulars", "amount", "remarks"
        )
        export_order = ("date", "short_no", "grant_no", "head", "particulars", "amount", "remarks")



class CommitmentResource(resources.ModelResource):
    grant_short_no =fields.Field(
         column_name="Grant Short No",
         attribute="grant_short_no"
    )
    
    date = fields.Field(
        column_name="Date",
        attribute="date",
        widget=FlexibleDateWidget()
    )

    # Explicitly define Foreignkey fields with widget
    seed_grant = fields.Field(
         attribute='seed_grant',
         widget=ForeignKeyWidget(SeedGrant, field='short_no')
    )

    tdg_grant = fields.Field(
         attribute ='tdg_grant',
         widget = ForeignKeyWidget(SeedGrant, field='short_no')
    )

    short_no = fields.Field(attribute="short_no", readonly = True)
   
    head = fields.Field(column_name="Commitment Head", attribute="head")
    particulars = fields.Field(column_name="Particulars", attribute="particulars")
    gross_amount = fields.Field(column_name="Gross Amount (in Rs.)", attribute="gross_amount")
    remarks = fields.Field(column_name="Remarks", attribute="remarks")
    grant_no = fields.Field(attribute="grant_no", readonly=True)

    def before_import_row(self, row, **kwargs):
        short_no_value = row.get("Grant Short No", "").strip()

        if not short_no_value:
            raise ValueError("Grant Short No is required but missing")
        
        
        seed_exists = SeedGrant.objects.get(short_no=short_no_value)
        if seed_exists:
            row["seed_grant"] = short_no_value
            row["tdg_grant"] = None
            return
        
        
        
        tdg_exists = TDGGrant.objects.get(short_no=short_no_value)
        if tdg_exists:
            row["tdg_grant"] = short_no_value
            row["seed_grant"] = None
            return
        

        raise ValueError(f"Grant with short_no '{short_no_value}' not found!")
    
    class Meta:
        model = Commitment
        exclude = ("id","seed_grant", "tdg_grant")  # don't include internal ID in Excel
        import_id_fields = []  # let Django auto-create IDs
        fields = (
            "date", 
            "short_no", "grant_no", "head",
            "particulars", "gross_amount", "remarks"
        )
        export_order = ("date","short_no", "grant_no", "head", "particulars", "gross_amount", "remarks")
