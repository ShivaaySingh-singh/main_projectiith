from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from .models import Faculty, Project, Receipt, SeedGrant, TDGGrant, Expenditure, Commitment
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login
import re
import urllib.parse


HEADS = [
    "Equipment", "Consumables", "Contingency", "Travel",
    "Manpower", "Others", "Furniture", "Visitor Expenses", "Lab Equipment"
]





def home(request):
    return render (request, "home.html")
# ✅ Faculty Dashboard  ( point to remeber humne comment kiya hai agar sab shi huaa to delete kar denge)
#@login_required
#def dashboard(request):
  #  faculty = get_object_or_404(Faculty, user=request.user)
    # Faculty ke projects filter karo
   # projects = Project.objects.filter(pi_email=faculty.email)
   # return render(request, 'dashboard.html', {'faculty': faculty, 'projects': projects})

# ✅ User Report View (readonly, screenshot style)
@login_required
def project_report(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Ensure all default heads exist
    default_heads = [
        "Manpower", "Contingency", "Travel", "Institute Overhead",
        "Consumable", "Equipment", "GST", "Research Personnel"
    ]
    receipts = []
    for head in default_heads:
        obj, created = Receipt.objects.get_or_create(project=project, category=head)
        receipts.append(obj)

    return render(request, "fund_report.html", {
        "project": project,
        "receipts": receipts,
    })


# ✅ Admin Save Fund Management
@login_required
def save_fund_management(request):
    if request.method == "POST":
        project_id = request.POST.get("project_id")
        project = get_object_or_404(Project, id=project_id)

        # Collect lists
        heads = request.POST.getlist("head_name")
        sanctions = request.POST.getlist("sanction_amount")
        openings = request.POST.getlist("opening_balance")
        receipts_list = request.POST.getlist("receipt")
        totals = request.POST.getlist("total")
        payments = request.POST.getlist("payments")
        balances_after = request.POST.getlist("balance_after_payment")
        committeds = request.POST.getlist("committed_bill")
        presents = request.POST.getlist("present_bill")
        balances = request.POST.getlist("balance")

        for i in range(len(heads)):
            Receipt.objects.update_or_create(
                project=project,
                category=heads[i],
                defaults={
                    "amount": float(sanctions[i] or 0),
                    "opening_balance": float(openings[i] or 0),
                    "receipt": float(receipts_list[i] or 0),
                    "total": float(totals[i] or 0),
                    "payments": float(payments[i] or 0),
                    "balance_after_payment": float(balances_after[i] or 0),
                    "committed_bill": float(committeds[i] or 0),
                    "present_bill": float(presents[i] or 0),
                    "balance": float(balances[i] or 0),
                }
            )

        messages.success(request, "Fund details saved successfully!")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


# 🔹 New System (SeedGrant + TDGGrant + Expenditure + Commitment)


# ✅ Updated Faculty Dashboard (Seed + TDG Grants)



@login_required
def dashboard(request):
    faculty = get_object_or_404(Faculty, user=request.user)

    # --- OLD SYSTEM ---
    projects = Project.objects.filter(faculty_id=faculty.faculty_id)

    # --- NEW SYSTEM (Seed + TDG) ---


    seed_projects = SeedGrant.objects.filter(faculty_id=faculty.faculty_id)
    tdg_projects = TDGGrant.objects.filter(faculty_id=faculty.faculty_id)

    for s in seed_projects:
        s.encoded_grant_no = urllib.parse.quote(s.grant_no, safe="")
    for t in tdg_projects:
        t.encoded_grant_no = urllib.parse.quote(t.grant_no, safe="")



    # --- TYPE FILTER LOGIC ---
    project_type = request.GET.get("type", "all")  # all / project / seed

    if project_type == "project":
        show_projects = True
        show_seed = False
        show_tdg = False
    elif project_type == "seed":
        show_projects = False
        show_seed = True
        show_tdg = True   # ✅ show both Seed + TDG together
    else:
        show_projects = True
        show_seed = True
        show_tdg = True   # ✅ default: show everything

    return render(request, "dashboard.html", {
        "faculty": faculty,
        "projects": projects,
        "seed_projects": seed_projects,
        "tdg_projects": tdg_projects,
        "project_type": project_type,
        "show_projects": show_projects,
        "show_seed": show_seed,
        "show_tdg": show_tdg,
    })


# ✅ Helper to prepare report
def prepare_report(project, expenditures, commitments):
    report_rows, total_budget, total_exp, total_commit = [], 0, 0, 0

    for head in HEADS:
        field_name = head.lower().replace(" ", "_")
        sanction = getattr(project, field_name, 0) or 0
        exp_sum = sum(exp.amount for exp in expenditures if exp.head.lower() == head.lower())
        commit_sum = sum(c.gross_amount for c in commitments if c.head.lower() == head.lower())
        balance = sanction - (exp_sum + commit_sum)

        total_budget += sanction
        total_exp += exp_sum
        total_commit += commit_sum

        report_rows.append({
            "head": head,
            "sanction": sanction,
            "expenditure": exp_sum,
            "commitment": commit_sum,
            "balance": balance
        })

    return report_rows, {
        "budget": total_budget,
        "expenditure": total_exp,
        "commitment": total_commit,
        "balance": total_budget - (total_exp + total_commit)
    }


# ✅ User Bill Report (readonly)
@login_required
def bill_report_user(request, grant_no):
    """
    Displays the report for a particular SeedGrant or TDGGrant.
    Fetches related Expenditure & Commitment via ForeignKey links (seed_grant/tdg_grant).
    """
    grant_no = urllib.parse.unquote(grant_no)
    grant = None
    project_type = None

    # 🔹 Identify which type of grant (Seed or TDG)
    try:
        grant = SeedGrant.objects.get(grant_no=grant_no)
        project_type = "Seed"
        # ✅ Fetch related expenditures and commitments via foreign key
        expenditures = Expenditure.objects.filter(seed_grant__grant_no=grant_no)
        commitments = Commitment.objects.filter(seed_grant__grant_no=grant_no)

    except SeedGrant.DoesNotExist:
        try:
            grant = TDGGrant.objects.get(grant_no=grant_no)
            project_type = "TDG"
            # ✅ Fetch related expenditures and commitments via foreign key
            expenditures = Expenditure.objects.filter(tdg_grant__grant_no=grant_no)
            commitments = Commitment.objects.filter(tdg_grant__grant_no=grant_no)
        except TDGGrant.DoesNotExist:
            # Grant not found
            messages.error(request, "Grant not found.")
            return redirect("dashboard")

    # 🔹 Prepare report
    report_rows, totals = prepare_report(grant, expenditures, commitments)

    return render(request, "bill_report_user.html", {
        "grant": grant,
        "project_type": project_type,
        "report_rows": report_rows,
        "expenditures": expenditures,
        "commitments": commitments,
        "totals": totals,
    })


@login_required
def bill_report_admin(request):
    """
    Admin report view for Seed & TDG grants.
    Uses dropdown to select grant and dynamically loads related data.
    """
    selected_grant, project_type = None, None
    expenditures, commitments = [], []

    report_rows = [{"head": head, "sanction": "", "expenditure": "", "commitment": "", "balance": ""} for head in HEADS]
    totals = {"budget": "", "expenditure": "", "commitment": "", "balance": ""}

    grant_no = request.GET.get("grant_no")

    if grant_no:
        # 🔹 Try fetching SeedGrant first
        try:
            selected_grant = SeedGrant.objects.get(grant_no=grant_no)
            project_type = "Seed"
            expenditures = Expenditure.objects.filter(seed_grant__grant_no=grant_no)
            commitments = Commitment.objects.filter(seed_grant__grant_no=grant_no)
        except SeedGrant.DoesNotExist:
            try:
                selected_grant = TDGGrant.objects.get(grant_no=grant_no)
                project_type = "TDG"
                expenditures = Expenditure.objects.filter(tdg_grant__grant_no=grant_no)
                commitments = Commitment.objects.filter(tdg_grant__grant_no=grant_no)
            except TDGGrant.DoesNotExist:
                selected_grant = None

        if selected_grant:
            report_rows, totals = prepare_report(selected_grant, expenditures, commitments)

    # 🔹 List all grant numbers for dropdown
    all_short_nos = list(SeedGrant.objects.values_list("grant_no", flat=True)) + \
                    list(TDGGrant.objects.values_list("grant_no", flat=True))

    # 🔹 Fallback: empty default grant if none selected
    if not selected_grant:
        selected_grant = SeedGrant(
            name="", dept="", title="", grant_no="",
            budget_year1=None, budget_year2=None, total_budget=None
        )

    return render(request, "admin/bill_report_admin.html", {
        "selected_grant": selected_grant,
        "project_type": project_type,
        "report_rows": report_rows,
        "expenditures": expenditures,
        "commitments": commitments,
        "totals": totals,
        "all_short_nos": all_short_nos
    })



@login_required
def get_seed_grant_details(request):
    """
    AJAX view: returns JSON data for a given Seed/TDG grant,
    including expenditure, commitment, and totals.
    """
    grant_no = request.GET.get("grant_no")
    if not grant_no:
        return JsonResponse({"error": "No grant_no provided"}, status=400)

    # 🔹 Detect which grant type
    try:
        grant = SeedGrant.objects.get(grant_no=grant_no)
        project_type = "Seed"
        expenditures_qs = Expenditure.objects.filter(seed_grant__grant_no=grant_no)
        commitments_qs = Commitment.objects.filter(seed_grant__grant_no=grant_no)
    except SeedGrant.DoesNotExist:
        try:
            grant = TDGGrant.objects.get(grant_no=grant_no)
            project_type = "TDG"
            expenditures_qs = Expenditure.objects.filter(tdg_grant__grant_no=grant_no)
            commitments_qs = Commitment.objects.filter(tdg_grant__grant_no=grant_no)
        except TDGGrant.DoesNotExist:
            return JsonResponse({"error": "Grant not found"}, status=404)

    report_rows, totals = prepare_report(grant, expenditures_qs, commitments_qs)

    expenditures = list(expenditures_qs.values("date", "head", "particulars", "amount", "remarks"))
    commitments = list(commitments_qs.values("date", "head", "gross_amount", "remarks"))

    data = {
        "name": grant.name,
        "dept": grant.dept,
        "title": grant.title,
        "grant_no": grant.grant_no,
        "year1_budget": getattr(grant, "budget_year1", None),
        "year2_budget": getattr(grant, "budget_year2", None),
        "total_budget": getattr(grant, "total_budget", None),
        "project_type": project_type,
        "report_rows": report_rows,
        "totals": totals,
        "expenditures": expenditures,
        "commitments": commitments,
    }

    return JsonResponse(data, encoder=DjangoJSONEncoder, safe=True)

#@login_required
#def redirect_after_login(request):
    """
    #Redirect user based on group membership after login.
    Faculty -> dashboard
    SheetsUsers -> sheets dashboard
    Others -> home
    """
    #user = request.user

    #if user.groups.filter(name='SheetsUsers').exists():
        #return redirect('/sheets_portal:dashboard')
    
    #if user.groups.filter(name='Faculty').exists():
        #return redirect('dashboard')
    
   # elif user.groups.filter(name='SheetsUsers').exists():
    #    return redirect('sheets_dashboard')
    #else:
     #   return redirect('home')
