from django.urls import path
from project import views
from django.urls import re_path
from .views import GenericModelAPIView, GenericModelDetailAPIView, upload_bill_pdf



urlpatterns = [
    path('', views.home, name='home'),

    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('project/<str:project_id>/', views.project_report, name='project_detail'),
    path("save-fund-management/", views.save_fund_management,name="save_fund_management"),
   
    path("bill-report-admin/", views.bill_report_admin, name="bill_report_admin"),
    re_path(r"^bill-report-user/(?P<grant_no>.+)/$", views.bill_report_user, name="bill_report_user"),
    path("get-seed-grant-details/", views.get_seed_grant_details, name="get_seed_grant_details"),
    path('api/<str:model_name>/', GenericModelAPIView.as_view(), name='api_model_list'),
    path('api/<str:model_name>/<str:pk>/', GenericModelDetailAPIView.as_view(), name='api_model_detail'),
    path('api/billinward/<int:pk>/upload_pdf/', upload_bill_pdf, name="upload_bill_bdf"),

    path('fund-request/create/', views.create_fund_request, name='create_fund_request'),
    path('fund-request/status/', views.request_status, name='request_status'),
    path('fund-request/get-projects/', views.get_projects_by_type, name='get_projects_by_type'),
    path('bill_inwards/', views.inward_bills_view, name='bill_inwards'),
    path("projects/<str:short_no>/balance-sheet/",views.project_balance_sheet, name="project_balance_sheet")
    
    

]







