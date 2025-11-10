
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from project import views as project_views
from project.admin import custom_admin_site


urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('', include('project.urls')),

    path('sheets/',  include('sheets_portal.urls')),



    # login/logout
     path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
     path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # password reset flow
    #path('password-reset/', 
         #auth_views.PasswordResetView.as_view(template_name="password_reset.html"), 
         #name="password_reset"),
    
    #path('password-reset/done/', 
         #auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"), 
         #name="password_reset_done"),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="password_reset.html"), 
         name="password_reset_confirm"),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), 
         name="password_reset_complete"),
]




