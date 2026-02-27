from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('verify/', views.verify_email, name='verify_email'),
    path('dash/', views.dashboard, name='user_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'), 

    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-panel/login/', views.admin_login, name='admin_login'),
    path('admin-panel/dashboard/', views.admin_dashboard, name='admin_dashboard'),
]