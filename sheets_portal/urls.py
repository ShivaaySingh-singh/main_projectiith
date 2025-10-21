from django.urls import path
from . import views

app_name = "sheets_portal"

urlpatterns = [
    path('dashboard/', views.sheets_dashboard, name='dashboard'),
    
]
