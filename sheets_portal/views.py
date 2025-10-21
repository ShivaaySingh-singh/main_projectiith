from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import GoogleSheet

@login_required
def sheets_dashboard(request):
    # Allow only SheetsUsers group members
    if not request.user.groups.filter(name='SheetsUsers').exists():
        return redirect('/')  # faculty shouldn't see this

    query = request.GET.get('q', '').strip()
    sheets = GoogleSheet.objects.filter(title__icontains=query) if query else GoogleSheet.objects.all()
    return render(request, 'sheets_portal/sheet_dashboard.html', {'sheets': sheets, 'query': query})
