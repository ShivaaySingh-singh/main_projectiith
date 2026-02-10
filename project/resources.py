from import_export import resources, fields
from .models import Faculty, Project, Receipt, SeedGrant, TDGGrant, Expenditure, Commitment,Payment, ReceiptHead, TDSSection, TDSRate
from import_export.widgets import DateWidget, ForeignKeyWidget
from datetime import datetime, date
import xlrd
from django.core.exceptions import ValidationError
from import_export.widgets import Widget
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist


class FundingObejctWidget(Widget):
    """
    Handles Project / SeedGrant /TDGGrant via short_no


    """

    MODEL_LOOKUP = [
        (SeedGrant, "short_no"),
        (TDGGrant, "short_no"),
        (Project, "project_short_no"),
    ]

    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        value = value.strip()

        for model, field in self.MODEL_LOOKUP:
            try:
                return model.objects.get(**{field: value})
            except ObjectDoesNotExist:
                continue

        raise ValueError(f"No Project / Grant fould for: {value}")
        
    def render(self, value, obj=None):
        if not value:
            return ""
            
        return str(value)



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
    project_start_date = fields.Field(column_name="Start Date", attribute="project_start_date", widget=FlexibleDateWidget())
    project_end_date = fields.Field(column_name="End Date", attribute="project_end_date", widget=FlexibleDateWidget())
    
    
    
    
    faculty_id = fields.Field(column_name="Faculty ID", attribute="faculty", widget=ForeignKeyWidget(Faculty, "faculty_id"))
    co_pi_name = fields.Field(column_name="Co PI Name", attribute="co_pi_name")
    pi_email = fields.Field(column_name="PI Email ID", attribute="pi_email")
    fellow_student_name = fields.Field(column_name="Fellow/Student Name", attribute="fellow_student_name")
    
    project_title = fields.Field(column_name="Project Title", attribute="project_title")
    country = fields.Field(column_name="Country", attribute="country")
    sponsoring_agency = fields.Field(column_name="Sponsoring Agency", attribute="sponsoring_agency")
    address_sponsoring_agency = fields.Field(column_name="Address of Sponsoring Agency", attribute="address_sponsoring_agency")
    pincode = fields.Field(column_name="Pincode", attribute="pincode")
    gst_no = fields.Field(column_name="GST No", attribute="gst_no")
    scheme_code = fields.Field(column_name="Scheme Code", attribute="scheme_code")
    scheme_name = fields.Field(column_name="Scheme Name", attribute="scheme_name")
    sanction_no = fields.Field(column_name="Sanction No.", attribute="sanction_number")
    sanction_date = fields.Field(column_name="Sanction Date", attribute="sanction_date", widget=FlexibleDateWidget())
    sanction_amount = fields.Field(column_name="Sanction Amount", attribute="sanction_amount")
    amount_to_be_received = fields.Field(column_name="Amount to be Received", attribute="amount_to_be_received")
    total_non_recurring = fields.Field(column_name="Total Non-Recurring", attribute="total_non_recurring")
    total_recurring = fields.Field(column_name="Total Recurring", attribute="total_recurring")

    # Bank & Remarks
    bank_name_account = fields.Field(column_name="Bank Name & A/C No", attribute="bank_name_account")
    remarks = fields.Field(column_name="Remarks", attribute="remarks")

    class Meta:
        model = Project
        import_id_fields = ["project_no"]
        skip_unchanged = True
        fields = (
            "project_short_no", "project_no", "gender", "project_type", "faculty_id",
            "co_pi_name", "pi_email", "project_title",
            "gst_no", "address_sponsoring_agency", "pincode", "sponsoring_agency", "country",
            "project_start_date", "project_end_date", 
            "fellow_student_name", "scheme_code", "scheme_name",
            "sanction_no", "sanction_date", "sanction_amount",
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
        column_name="Date", attribute="receipt_date", widget=FlexibleDateWidget()
    )
    
    category = fields.Field(column_name="Category", attribute="category")
    reference_number = fields.Field(column_name="Reference Number", attribute="reference_number")
    amount = fields.Field(column_name="Sanction Amount", attribute="amount")
    head = fields.Field(column_name="Head", attribute="head", widget=ForeignKeyWidget(ReceiptHead, "name"))
    

    class Meta:
        model = Receipt
        import_id_fields = ["project", "receipt_date", "head", "amount"]

        fields = ("project", "receipt_date","category", "reference_number", "head", "amount",)
        export_order = fields


class SeedGrantResource(resources.ModelResource):
    short_no = fields.Field(column_name="Seed grant short no", attribute="short_no")
    grant_no = fields.Field(column_name="Seed Grant no", attribute="grant_no")
    faculty = fields.Field(column_name="Faculty ID", attribute="faculty", widget=ForeignKeyWidget(Faculty, 'faculty_id'))
    
    
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
        import_id_fields = ["short_no"]
        skip_unchanged = True
        fields =(
            "grant_no", "short_no", "title", "faculty",
            "sanction_date", "end_date", "budget_year1", "budget_year2",
            "total_budget", "equipment", "consumables", "contingency",
            "travel", "manpower", "others", "furniture",
            "visitor_expenses", "lab_equipment"

        )
        


class TDGGrantResource(resources.ModelResource):
    short_no = fields.Field(column_name="Technology Development short no", attribute="short_no")
    grant_no = fields.Field(column_name="Technology Development Grant no", attribute="grant_no")
    faculty = fields.Field(column_name="Faculty ID", attribute="faculty", widget=ForeignKeyWidget(Faculty, 'faculty_id'))
    
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
        import_id_fields = ["short_no"]
        skip_unchanged = True
        fields =(
            "grant_no", "short_no", "title", "faculty",
            "sanction_date", "end_date", "budget_year1", "budget_year2",
            "total_budget", "equipment", "consumables", "contingency",
            "travel", "manpower", "others", "furniture",
            "visitor_expenses", "lab_equipment"

        )
        



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
         widget=ForeignKeyWidget(SeedGrant, field='id')
     )

     tdg_grant = fields.Field(
         attribute ='tdg_grant',
         widget = ForeignKeyWidget(TDGGrant, field='id')
     )

     project = fields.Field(
         attribute='project',
         widget=ForeignKeyWidget(Project, field='id')
         
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
            
            
            seed = SeedGrant.objects.filter(short_no=short_no_value).first()
            if seed:
                row["seed_grant"] = seed.id
                row["tdg_grant"] = None
                row["project"] = None
                return
            
            tdg = TDGGrant.objects.filter(short_no=short_no_value).first()
            if tdg:
                row["tdg_grant"] = tdg.id
                row["seed_grant"] = None
                row["project"] = None
                return
           
            proj = Project.objects.filter(project_no=short_no_value).first()
            if proj:
                row["project"] = proj.id
                row["seed_grant"] = None
                row["tdg_grant"] = None
                return

            raise ValueError(f"Grant with Short_no '{short_no_value}' not found in Seed or TDG")
     
     class Meta:
        model = Expenditure
        exclude = ("id",)  # don't include internal ID in Excel
        import_id_fields = []  # let Django auto-create IDs
        skip_unchanged = True
        fields = (
            "date", "seed_grant", "tdg_grant", "project",
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
         widget=ForeignKeyWidget(SeedGrant, field='id')
    )

    tdg_grant = fields.Field(
         attribute ='tdg_grant',
         widget = ForeignKeyWidget(SeedGrant, field='id')
    )

    project = fields.Field(
        attribute='project',
        widget=ForeignKeyWidget(Project, field='id')
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
        
        
        seed = SeedGrant.objects.filter(short_no=short_no_value).first()
        if seed:
            row["seed_grant"] = seed.id
            row["tdg_grant"] = None
            row["project"] = None
            return
        
        
        
        tdg = TDGGrant.objects.filter(short_no=short_no_value).first()
        if tdg:
            row["tdg_grant"] = tdg.id
            row["seed_grant"] = None
            row["project"] = None
            return
        
        proj = Project.objects.filter(project_no=short_no_value).first()
        if proj:
            row["project"] = proj.id
            row["seed_grant"] = None
            row["tdg_grant"] = None

        raise ValueError(f"Grant with short_no '{short_no_value}' not found!")
    
    class Meta:
        model = Commitment
        exclude = ("id",)  # don't include internal ID in Excel
        import_id_fields = []  # let Django auto-create IDs
        fields = (
            "date", "seed_grant", "tdg_grant", "project",
            "short_no", "grant_no", "head",
            "particulars", "gross_amount", "remarks"
        )
        export_order = ("date","short_no", "grant_no", "head", "particulars", "gross_amount", "remarks")


from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import (
    Payment, Project, ReceiptHead,
    Payee, PaymentType, Bank,
    TDSSection, TDSRate
)



class PaymentResource(resources.ModelResource):

    # -------------------------
    # Core references
    # -------------------------
    funding_object = fields.Field(
        column_name="Project No",
        attribute="funding_object",
        widget=FundingObejctWidget()

    )
    

    head = fields.Field(
        column_name="Head",
        attribute="head",
        widget=ForeignKeyWidget(ReceiptHead, "name")
    )

    payment_type = fields.Field(
        column_name="Payment Type",
        attribute="payment_type",
        widget=ForeignKeyWidget(PaymentType, "name")
    )

    payee = fields.Field(
        column_name="Payee PAN",
        attribute="payee",
        widget=ForeignKeyWidget(Payee, "pan")
    )

    bank = fields.Field(
        column_name="Bank",
        attribute="bank",
        widget=ForeignKeyWidget(Bank, "short_no")
    )

    # -------------------------
    # Date
    # -------------------------
    date = fields.Field(
        column_name="Date",
        attribute="date",
        widget=FlexibleDateWidget()
    )

    # -------------------------
    # Transaction identifiers
    # -------------------------
    utr_no = fields.Field(
        column_name="UTR No",
        attribute="utr_no"
    )

    cheque_no = fields.Field(
        column_name="Cheque No",
        attribute="cheque_no"
    )

    # -------------------------
    # Amounts (IMPORT AS-IS)
    # -------------------------
    amount = fields.Field(
        column_name="Amount",
        attribute="amount"
    )

    tds_section = fields.Field(
        column_name="Tax U/S",
        attribute="tds_section",
        widget=ForeignKeyWidget(TDSSection, "section")
    )

    tds_rate = fields.Field(
        column_name="TDS %",
        attribute="tds_rate",
        widget=ForeignKeyWidget(TDSRate, "percent")
    )

    tds_amount = fields.Field(
        column_name="TDS Amount",
        attribute="tds_amount"
    )

    gst_tds_type = fields.Field(
        column_name="GST-TDS Type",
        attribute="gst_tds_type"
    )

    igst_tds = fields.Field(
        column_name="IGST-TDS",
        attribute="igst_tds"
    )

    cgst_tds = fields.Field(
        column_name="CGST-TDS",
        attribute="cgst_tds"
    )

    sgst_tds = fields.Field(
        column_name="SGST-TDS",
        attribute="sgst_tds"
    )

    net_amount = fields.Field(
        column_name="Net Amount",
        attribute="net_amount"
    )

    purpose = fields.Field(
        column_name="Purpose",
        attribute="purpose"
    )

    # -------------------------
    # Meta
    # -------------------------
    class Meta:
        model = Payment
        import_id_fields = ("id",)
        skip_unchanged = True

        fields = (
            "id",
            "date",
            "funding_object",
            "head",
            "payment_type",
            "payee",
            "bank",
            "utr_no",
            "cheque_no",
            "amount",
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

        export_order = fields
