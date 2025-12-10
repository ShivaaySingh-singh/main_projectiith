from import_export import resources, fields
from .models import Faculty, Project, Receipt, SeedGrant, TDGGrant, Expenditure, Commitment,Payment, ReceiptHead, TDSSection, TDSRate
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
    project_short_no = fields.Field(column_name="Project Short No", attribute="project_short_no")
    project_no = fields.Field(column_name="Project No.", attribute="project_no")
    gender = fields.Field(column_name="Gender", attribute="gender")
    project_type = fields.Field(column_name="Project Type", attribute="project_type")
    project_start_date = fields.Field(column_name="Start Date", attribute="start_date", widget=FlexibleDateWidget())
    project_end_date = fields.Field(column_name="End Date", attribute="end_date", widget=FlexibleDateWidget())
    is_extended = fields.Field(column_name="Is Extended", attribute="is_extended")
    extended_end_date = fields.Field(column_name="Extended End Date", attribute="extended_end_date",widget=FlexibleDateWidget())
    project_status = fields.Field(column_name="Status", attribute="project_status")
    pi_name = fields.Field(column_name="PI Name", attribute="pi_name")
    faculty_id = fields.Field(column_name="Faculty ID", attribute="faculty_id")
    co_pi_name = fields.Field(column_name="Co PI Name", attribute="co_pi_name")
    pi_email = fields.Field(column_name="PI Email ID", attribute="pi_email")
    fellow_student_name = fields.Field(column_name="Fellow/Student Name", attribute="fellow_student_name")
    department = fields.Field(column_name="Department", attribute="department")
    project_title = fields.Field(column_name="Project Title", attribute="project_title")
    country = fields.Field(column_name="Country", attribute="country")
    sponsoring_agency = fields.Field(column_name="Sponsoring Agency", attribute="sponsoring_agency")
    address_sponsoring_agency = fields.Field(column_name="Address of Sponsoring Agency", attribute="address_sponsoring_agency")
    pincode = fields.Field(column_name="Pincode", attribute="pincode")
    gst_no = fields.Field(column_name="GST No", attribute="gst_no")
    sanction_no = fields.Field(column_name="Sanction No.", attribute="sanction_no")
    sanction_date = fields.Field(column_name="Sanction Date", attribute="sanction_date", widget=FlexibleDateWidget())
    amount_to_be_received = fields.Field(column_name="Amount to be Received", attribute="amount_to_be_received")
    total_non_recurring = fields.Field(column_name="Total Non-Recurring", attribute="total_non_recurring")
    total_recurring = fields.Field(column_name="Total Recurring", attribute="total_recurring")

    # Bank & Remarks
    bank_name_account = fields.Field(column_name="Bank Name & A/C No", attribute="bank_name_account")
    remarks = fields.Field(column_name="Remarks", attribute="remarks")

    class Meta:
        model = Project
        import_id_fields = ["project_no"]
        skip_unchnaged = True
        fields = (
            "project_short_no", "project_no", "gender", "project_type", "faculty_id",
            "pi_name", "co_pi_name", "pi_email", "department", "project_title",
            "gst_no", "address_sponsoring_agency", "pincode", "sponsoring_agency", "country",
            "project_start_date", "project_end_date", "is_extended", "extended_end_date", "project_status",
            "fellow_student_name", "scheme_code", "scheme_name",
            "sanction_number", "sanction_date", "sanction_amount",
            "amount_to_be_received", "total_non_recurring", "total_recurring",
            "bank_name_account", "remarks",
        )


# ✅ Receipt Resource
class ReceiptResource(resources.ModelResource):
    project = fields.Field(
        column_name="Project No.",
        attribute="project",
        widget=resources.widgets.ForeignKeyWidget(Project, "project_no")
    )
    receipt_date = fields.Field(
        column_name="Date", attribute="reciept_date", widget=FlexibleDateWidget()
    )
    fy = fields.Field(column_name="Financial Year", attribute="fy")
    category = fields.Field(column_name="Category", attribute="category")
    reference_number = fields.Field(column_name="Reference Number", attribute="reference_number")
    amount = fields.Field(column_name="Sanction Amount", attribute="amount")
    head = fields.Field(column_name="Head", attribute="head", widget=ForeignKeyWidget(ReceiptHead, "name"))
    

    class Meta:
        model = Receipt
        import_id_fields = ["project", "receipt_date", "head", "amount"]

        fields = ("project", "receipt_date", "fy", "category", "reference_number", "head", "amount",)
        export_order = fields


class SeedGrantResource(resources.ModelResource):
    short_no = fields.Field(column_name="Seed grant short no", attribute="short_no")
    grant_no = fields.Field(column_name="Seed Grant no", attribute="grant_no")
    faculty = fields.Field(column_name="Faculty ID", attribute="faculty", widget=ForeignKeyWidget(Faculty, 'faculty_id'))
    pi_name = fields.Field(column_name=" PI Name", attribute="pi_name")
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
            "grant_no", "short_no", "pi_name", "dept", "title", "faculty",
            "sanction_date", "end_date", "budget_year1", "budget_year2",
            "total_budget", "equipment", "consumables", "contingency",
            "travel", "manpower", "others", "furniture",
            "visitor_expenses", "lab_equipment"

        )
        export_order = fields

    def dehydrate_pi_name(self, obj):
        return obj.faculty.pi_name if obj.faculty else ""
    
    def dehydrate_dept(self, obj):
        return obj.faculty.department if obj.faculty else ""
        
    def dehydrate_faculty(self, obj):
        return obj.faculty.faculty_id if obj.faculty else ""


class TDGGrantResource(resources.ModelResource):
    short_no = fields.Field(column_name="Technology Development short no", attribute="short_no")
    grant_no = fields.Field(column_name="Technology Development Grant no", attribute="grant_no")
    faculty = fields.Field(column_name="Faculty ID", attribute="faculty", widget=ForeignKeyWidget(Faculty, 'faculty_id'))
    pi_name = fields.Field(column_name=" PI Name", attribute="pi_name")
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
            "grant_no", "short_no", "pi_name", "dept", "title", "faculty",
            "sanction_date", "end_date", "budget_year1", "budget_year2",
            "total_budget", "equipment", "consumables", "contingency",
            "travel", "manpower", "others", "furniture",
            "visitor_expenses", "lab_equipment"

        )
        export_order = fields

        def dehydrate_pi_name(self, obj):
            return obj.faculty.pi_name if obj.faculty else ""
    
        def dehydrate_dept(self, obj):
            return obj.faculty.department if obj.faculty else ""
        
        def dehydrate_faculty(self, obj):
            return obj.faculty.faculty_id if obj.faculty else ""



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


class PaymentResource(resources.ModelResource):
    project = fields.Field(column_name="Project No", attribute="project", widget=ForeignKeyWidget(Project, "project_no"))
    head = fields.Field(column_name="Head", attribute="head", widget=ForeignKeyWidget(ReceiptHead, "name"))
    tds_section = fields.Field(column_name="Tax U/S", attribute="tds_section", widget=ForeignKeyWidget(TDSSection, "section"))
    
    tds_rate = fields.Field(
        column_name="TDS %",
        attribute="tds_rate",
        widget=ForeignKeyWidget(TDSRate, "rate")   # update according to your model
    )

    # Date field
    date = fields.Field(
        column_name="Date",
        attribute="date",
        widget=FlexibleDateWidget()
    )

    # Normal fields
    payment_type = fields.Field(column_name="Payment Type", attribute="payment_type")
    name_of_payee = fields.Field(column_name="Payee Name", attribute="name_of_payee")

    bank_name = fields.Field(column_name="Bank Name", attribute="bank_name")
    branch = fields.Field(column_name="Branch", attribute="branch")
    account_no = fields.Field(column_name="Account No", attribute="account_no")
    ifsc = fields.Field(column_name="IFSC", attribute="ifsc")

    utr_no = fields.Field(column_name="UTR No", attribute="utr_no")
    faculty_id = fields.Field(column_name="Faculty ID", attribute="faculty_id", widget=ForeignKeyWidget(Faculty, 'faculty_id'))
    pi_name = fields.Field(column_name="PI Name", attribute="pi_name")

    tds_amount = fields.Field(column_name="TDS Amount", attribute="tds_amount")

    gst_tds_type = fields.Field(column_name="GST-TDS Type", attribute="gst_tds_type")
    igst_tds = fields.Field(column_name="IGST-TDS", attribute="igst_tds")
    cgst_tds = fields.Field(column_name="CGST-TDS", attribute="cgst_tds")
    sgst_tds = fields.Field(column_name="SGST-TDS", attribute="sgst_tds")

    net_amount = fields.Field(column_name="Net Amount", attribute="net_amount")
    purpose = fields.Field(column_name="Purpose", attribute="purpose")

    class Meta:
        model = Payment
        import_id_fields = ["id"]     # safest choice (reference/utr blank ho sakta)
        skip_unchanged = True
        fields = (
            "id",
            "date",
            "project",
            "head",
            "payment_type",
            "name_of_payee",
            "bank_name",
            "branch",
            "account_no",
            "ifsc",
            "utr_no",
            "faculty_id",
            "pi_name",
            "tds_section",
            "tds_rate",
            "tds_amount",
            "gst_tds_type",
            "igst_tds",
            "cgst_tds",
            "sgst_tds",
            "net_amount",
            "purpose",
        )
    def dehydrate_pi_name(self, obj):
        return obj.faculty.pi_name if obj.faculty else ""
 
        
    def dehydrate_faculty(self, obj):
        return obj.faculty.faculty_id if obj.faculty else ""