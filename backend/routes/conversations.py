"""
Conversation routes — CRUD for conversations.
Thin handlers that delegate to conversation_service.
"""

from flask import Blueprint, jsonify, g

from backend.middleware.auth import require_auth
from backend.services import conversation_service

conversations_bp = Blueprint("conversations", __name__)


@conversations_bp.get("/conversations")
@require_auth
def list_conversations():
    """List all conversations for the authenticated user."""
    conversations = conversation_service.list_for_user(g.user_id)
    return jsonify({"conversations": conversations})


@conversations_bp.get("/conversations/<int:conv_id>")
@require_auth
def get_conversation(conv_id):
    """Load all messages for a specific conversation."""
    conv, messages = conversation_service.get_with_messages(conv_id, g.user_id)
    if conv is None:
        return jsonify({"error": "Conversation not found"}), 404

    return jsonify({"conversation": conv, "messages": messages})


@conversations_bp.delete("/conversations/<int:conv_id>")
@require_auth
def delete_conversation(conv_id):
    """Delete a conversation and all its messages."""
    deleted = conversation_service.delete(conv_id, g.user_id)
    if not deleted:
        return jsonify({"error": "Conversation not found"}), 404

    return jsonify({"success": True})
