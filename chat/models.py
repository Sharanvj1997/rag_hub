from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """A conversation thread, so a user can have multiple separate chats."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )

    title = models.CharField(max_length=255, default="New Chat")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.owner.email})"


class Message(models.Model):
    """A single message within a session — either from the user or the assistant."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(max_length=10, choices=Role.choices)

    content = models.TextField()

    # Stores which document chunks were used to answer this message,
    # so citations can be shown later ("answered using: resume.pdf, chunk 3").
    source_chunks = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"