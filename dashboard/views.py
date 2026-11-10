from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from documents.models import Document
from chat.models import ChatSession


def dashboard_page(request):
    return render(request, "dashboard/dashboard.html")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats(request):
    docs = Document.objects.filter(owner=request.user)
    return Response({
        "success": True,
        "data": {
            "documents": docs.count(),
            "documents_ready": docs.filter(status=Document.Status.READY).count(),
            "chat_sessions": ChatSession.objects.filter(owner=request.user).count(),
        },
    })