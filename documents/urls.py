from django.urls import path
from . import views

urlpatterns = [
    path('',views.documents_page, name='documents-page'),
    path("list/", views.list_documents, name="api-documents-list"),
    path("upload/", views.upload_document, name="api-documents-upload"),
    path("<int:pk>/delete/", views.delete_document, name="api-documents-delete"),
]