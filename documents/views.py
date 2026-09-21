from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, get_object_or_404

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer


# ---------- Page view ----------

def documents_page(request):
    return render(request, "documents/documents.html")


# ---------- API views ----------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_documents(request):
    """Returns only the logged-in user's documents."""
    print('calling list_documents API view')
    documents = Document.objects.filter(owner=request.user)
    serializer = DocumentSerializer(documents, many=True, context={"request": request})
    return Response({"success": True, "data": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_document(request):
    serializer = DocumentUploadSerializer(
        data=request.data, context={"request": request}
    )

    if serializer.is_valid():
        document = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Document uploaded successfully.",
                "data": DocumentSerializer(document, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {"success": False, "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_document(request, pk):
    from rag.vectorstore import delete_document_chunks

    document = get_object_or_404(Document, pk=pk, owner=request.user)
    delete_document_chunks(document.id)   # <-- remove orphaned vectors first
    document.file.delete(save=False)
    document.delete()

    return Response(
        {"success": True, "message": "Document deleted."},
        status=status.HTTP_200_OK,
    )





from .tasks import process_document_task

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_document(request):
    serializer = DocumentUploadSerializer(
        data=request.data, context={"request": request}
    )

    if serializer.is_valid():
        document = serializer.save()

        process_document_task.delay(document.id)   # <-- fires the background task

        return Response(
            {
                "success": True,
                "message": "Document uploaded successfully.",
                "data": DocumentSerializer(document, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {"success": False, "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )