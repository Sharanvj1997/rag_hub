from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts import views as accounts_views
from chat import views as chat_views
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # page views
    path('register/', accounts_views.register_page, name='register-page'),
    path('login/', accounts_views.login_page, name='login-page'),
    path('dashboard/', include('dashboard.urls')),
    path('documents/', include('documents.urls')),
    path('chat/', chat_views.chat_page, name='chat-page'),
    path('api/chat/', include('chat.urls')),

    # API
    path('api/accounts/', include('accounts.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/dashboard/stats/', dashboard_views.stats, name='api-dashboard-stats'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)