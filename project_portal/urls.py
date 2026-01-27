
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from project import views as project_views
from project.admin import custom_admin_site
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('', include('project.urls')),

    path('sheets/',  include('sheets_portal.urls')),

    


    # login/logout
     path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
     path('logout/', auth_views.LogoutView.as_view(), name='logout'), 
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="password_reset.html"), 
         name="password_reset_confirm"),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_confirm.html"), 
         name="password_reset_complete"),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




