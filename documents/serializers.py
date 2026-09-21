import os
from rest_framework import serializers
from .models import Document

ALLOWED_EXTENSIONS = [".pdf", ".txt", ".md"]
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class DocumentSerializer(serializers.ModelSerializer):
    """Used for listing documents."""

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "file",
            "file_type",
            "size_bytes",
            "status",
            "error_message",
            "uploaded_at",
        )
        read_only_fields = fields


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Used for the upload endpoint."""

    class Meta:
        model = Document
        fields = ("id", "title", "file")
        read_only_fields = ("id",)

    def validate_file(self, value):
        ext = os.path.splitext(value.name)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Allowed types: "
                f"{', '.join(ALLOWED_EXTENSIONS)}"
            )

        if value.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(
                f"File too large. Max size is {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
            )

        return value

    def create(self, validated_data):
        file = validated_data["file"]
        ext = os.path.splitext(file.name)[1].lower().lstrip(".")

        return Document.objects.create(
            owner=self.context["request"].user,
            title=validated_data.get("title") or file.name,
            file=file,
            file_type=ext,
            size_bytes=file.size,
            status=Document.Status.PENDING,
        )