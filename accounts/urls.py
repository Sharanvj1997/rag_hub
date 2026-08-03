from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("register/", views.register_user, name="api-register"),
    path("login/", views.LoginView.as_view(), name="api-login"),
    path("login/refresh/", TokenRefreshView.as_view(), name="api-login-refresh"),
    path("logout/", views.logout_user, name="api-logout"),
]