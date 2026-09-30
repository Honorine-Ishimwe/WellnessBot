"""
Chat routes — sync and streaming chat endpoints.
Thin handlers that delegate to chat_service.
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context, g

from backend.middleware.auth import require_auth
from backend.services import chat_service

chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/chat")
@require_auth
def chat():
    """Synchronous chat endpoint."""
    data = request.get_json(force=True) or {}
    user_message = chat_service.sanitize_input((data.get("message") or "").strip())
    mood = (data.get("mood") or "").strip() or None
    conversation_id = data.get("conversation_id")

    if not user_message:
        return jsonify({"reply": "I didn't catch that. Could you say it again?"})

    reply, conversation_id, error_status = chat_service.process_message(
        user_id=g.user_id,
        user_message=user_message,
        mood=mood,
        conversation_id=conversation_id,
    )

    if error_status:
        return jsonify({"reply": reply, "conversation_id": conversation_id}), error_status

    return jsonify({"reply": reply, "conversation_id": conversation_id})


@chat_bp.post("/chat/stream")
@require_auth
def chat_stream():
    """Streaming chat endpoint using Server-Sent Events."""
    data = request.get_json(force=True) or {}
    user_message = chat_service.sanitize_input((data.get("message") or "").strip())
    mood = (data.get("mood") or "").strip() or None
    conversation_id = data.get("conversation_id")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    return Response(
        stream_with_context(
            chat_service.stream_message(
                user_id=g.user_id,
                user_message=user_message,
                mood=mood,
                conversation_id=conversation_id,
            )
        ),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
