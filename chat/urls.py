from django.urls import path
from . import views

urlpatterns = [
    path("sessions/", views.list_sessions, name="api-chat-sessions-list"),
    path("sessions/create/", views.create_session, name="api-chat-sessions-create"),
    path("sessions/<int:session_id>/", views.session_detail, name="api-chat-session-detail"),
    path("sessions/<int:session_id>/messages/", views.get_session_messages, name="api-chat-messages"),
    path("sessions/<int:session_id>/stream/", views.stream_chat_response, name="api-chat-stream"),
]