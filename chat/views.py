import json

from django.http import StreamingHttpResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from documents.models import Document
from rag.llm import generate_response
from rag.prompts import build_rag_prompt
from rag.retrieval import retrieve_relevant_chunks
from .models import ChatSession, Message


def chat_page(request):
    return render(request, "chat/chat.html")


def serialize_session(session):
    return {
        "id": session.id,
        "title": session.title,
        "updated_at": session.updated_at,
        "document_ids": [d.id for d in session.documents.all()],
    }


def set_session_documents(session, user, document_ids):
    """Only the owner's processed documents can be attached to a chat."""
    try:
        ids = [int(i) for i in (document_ids or [])]
    except (TypeError, ValueError):
        ids = []
    docs = Document.objects.filter(id__in=ids, owner=user, status=Document.Status.READY)
    session.documents.set(docs)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_sessions(request):
    sessions = ChatSession.objects.filter(owner=request.user).prefetch_related("documents")
    return Response({"success": True, "data": [serialize_session(s) for s in sessions]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_session(request):
    session = ChatSession.objects.create(owner=request.user, title="New Chat")
    set_session_documents(session, request.user, request.data.get("document_ids"))
    return Response(
        {"success": True, "data": serialize_session(session)},
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def session_detail(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, owner=request.user)

    if request.method == "DELETE":
        session.delete()
        return Response({"success": True, "message": "Chat deleted."})

    if "document_ids" in request.data:
        set_session_documents(session, request.user, request.data.get("document_ids"))
    return Response({"success": True, "data": serialize_session(session)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_session_messages(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, owner=request.user)
    data = [
        {
            "role": m.role,
            "content": m.content,
            "source_chunks": m.source_chunks,
            "created_at": m.created_at,
        }
        for m in session.messages.all()
    ]
    return Response({"success": True, "session": serialize_session(session), "data": data})


def _sse_error(message, http_status):
    return StreamingHttpResponse(
        iter([f"data: {json.dumps({'error': message})}\n\n"]),
        content_type="text/event-stream",
        status=http_status,
    )


def stream_chat_response(request, session_id):
    # Plain Django view (not DRF): EventSource can't send headers, so the JWT arrives as ?token=
    token = request.GET.get("token")
    if not token:
        return _sse_error("Missing token", 401)

    try:
        auth = JWTAuthentication()
        user = auth.get_user(auth.get_validated_token(token))
    except (InvalidToken, AuthenticationFailed):
        return _sse_error("Invalid or expired token", 401)

    query = request.GET.get("message", "").strip()
    if not query:
        return _sse_error("Empty message", 400)

    session = get_object_or_404(ChatSession, id=session_id, owner=user)

    Message.objects.create(session=session, role=Message.Role.USER, content=query)

    # First question becomes the chat title; save() also bumps updated_at
    if session.title == "New Chat":
        session.title = query[:40]
    session.save(update_fields=["title", "updated_at"])

        # Fewer history turns keeps a small local model focused (and stops it copying its own old mistakes)
    recent = list(session.messages.order_by("-created_at")[1:5])  # skip the message just created
    recent.reverse()
    chat_history = [{"role": m.role, "content": m.content} for m in recent]

    selected_docs = list(session.documents.all())
    selected_ids = [d.id for d in selected_docs]
    selected_titles = [d.title for d in selected_docs]

    chunks = retrieve_relevant_chunks(query, user_id=user.id, document_ids=selected_ids or None)

    titles = {
        d.id: d.title
        for d in Document.objects.filter(owner=user, id__in={c["document_id"] for c in chunks})
    }
    for c in chunks:
        c["title"] = titles.get(c["document_id"])

    prompt = build_rag_prompt(
        query, chunks, chat_history=chat_history, selected_titles=selected_titles
    )
    source_titles = list(dict.fromkeys(c["title"] for c in chunks if c.get("title")))

    def event_stream():
        full_response = ""
        try:
            yield f"data: {json.dumps({'sources': source_titles})}\n\n"
            for piece in generate_response(prompt, stream=True):
                full_response += piece
                yield f"data: {json.dumps({'token': piece})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if full_response:
                Message.objects.create(
                    session=session,
                    role=Message.Role.ASSISTANT,
                    content=full_response,
                    source_chunks=[
                        {
                            "document_id": c["document_id"],
                            "chunk_index": c["chunk_index"],
                            "title": c.get("title"),
                        }
                        for c in chunks
                    ],
                )
            yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response