from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """A conversation thread. Optionally scoped to specific documents."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )

    title = models.CharField(max_length=255, default="New Chat")

    # Empty selection means "search all of the user's documents"
    documents = models.ManyToManyField(
        "documents.Document",
        blank=True,
        related_name="chat_sessions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.owner.email})"


class Message(models.Model):
    """A single message within a session, either from the user or the assistant."""

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

    # Which document chunks were used to answer this message (for citations)
    source_chunks = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"