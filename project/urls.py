from django.urls import path
from project import views
from django.urls import re_path


urlpatterns = [
    path('', views.home, name='home'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('project/<int:project_id>/', views.project_report, name='project_detail'),
    path("save-fund-management/", views.save_fund_management,name="save_fund_management"),
   
    path("bill-report-admin/", views.bill_report_admin, name="bill_report_admin"),
    re_path(r"^bill-report-user/(?P<grant_no>.+)/$", views.bill_report_user, name="bill_report_user"),
    path("get-seed-grant-details/", views.get_seed_grant_details, name="get_seed_grant_details"),

]







