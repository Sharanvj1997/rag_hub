# from django.db import models
# from django.contrib.auth.models import User


# class Document(models.Model):

#     STATUS_CHOICES = [
#         ("UPLOADED", "Uploaded"),
#         ("PROCESSING", "Processing"),
#         ("PROCESSED", "Processed"),
#         ("FAILED", "Failed"),
#     ]

#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="documents"
#     )

#     title = models.CharField(max_length=255)

#     file = models.FileField(
#         upload_to="documents/"
#     )

#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default="UPLOADED"
#     )

#     uploaded_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     def __str__(self):
#         return self.title