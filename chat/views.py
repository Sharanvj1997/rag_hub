import json
from django.http import StreamingHttpResponse
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import ChatSession, Message
from rag.retrieval import retrieve_relevant_chunks
from rag.prompts import build_rag_prompt
from rag.llm import generate_response


# ---------- Page view ----------

def chat_page(request):
    return render(request, "chat/chat.html")


# ---------- Session management ----------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_sessions(request):
    sessions = ChatSession.objects.filter(owner=request.user)
    data = [
        {"id": s.id, "title": s.title, "updated_at": s.updated_at}
        for s in sessions
    ]
    return Response({"success": True, "data": data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_session(request):
    session = ChatSession.objects.create(owner=request.user, title="New Chat")
    return Response(
        {"success": True, "data": {"id": session.id, "title": session.title}},
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_session_messages(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, owner=request.user)
    messages = session.messages.all()
    data = [
        {"role": m.role, "content": m.content, "created_at": m.created_at}
        for m in messages
    ]
    return Response({"success": True, "data": data})


# ---------- The actual streaming chat endpoint ----------
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

def stream_chat_response(request, session_id):
    token = request.GET.get("token")

    if not token:
        return StreamingHttpResponse(
            iter(['data: {"error": "Missing token"}\n\n']),
            content_type="text/event-stream",
            status=401,
        )

    try:
        validated_token = JWTAuthentication().get_validated_token(token)
        user = JWTAuthentication().get_user(validated_token)
    except InvalidToken:
        return StreamingHttpResponse(
            iter(['data: {"error": "Invalid or expired token"}\n\n']),
            content_type="text/event-stream",
            status=401,
        )

    query = request.GET.get("message", "").strip()
    if not query:
        return StreamingHttpResponse(
            iter(['data: {"error": "Empty message"}\n\n']),
            content_type="text/event-stream",
            status=400,
        )

    session = get_object_or_404(ChatSession, id=session_id, owner=user)

    Message.objects.create(session=session, role=Message.Role.USER, content=query)

    recent_messages = list(
        session.messages.order_by("-created_at")[1:7]  # skip the one just created
    )
    recent_messages.reverse()
    chat_history = [{"role": m.role, "content": m.content} for m in recent_messages]

    chunks = retrieve_relevant_chunks(query, user_id=user.id)
    prompt = build_rag_prompt(query, chunks, chat_history=chat_history)

    def event_stream():
        full_response = ""
        try:
            for token_piece in generate_response(prompt, stream=True):
                full_response += token_piece
                payload = json.dumps({"token": token_piece})
                yield f"data: {payload}\n\n"
        except Exception as e:
            error_payload = json.dumps({"error": str(e)})
            yield f"data: {error_payload}\n\n"
        finally:
            if full_response:
                Message.objects.create(
                    session=session,
                    role=Message.Role.ASSISTANT,
                    content=full_response,
                    source_chunks=[
                        {"document_id": c["document_id"], "chunk_index": c["chunk_index"]}
                        for c in chunks
                    ],
                )
            yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response