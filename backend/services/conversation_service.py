"""
Conversation service — business logic for conversation CRUD.
No Flask imports — pure Python logic.
"""

from backend.repositories import conversation_repo, message_repo


def create(user_id, user_message, mood=None):
    """Create a new conversation with auto-generated title."""
    title = user_message[:50] + ("…" if len(user_message) > 50 else "")
    return conversation_repo.create(user_id, title, mood)


def list_for_user(user_id):
    """List all conversations for a user, with ISO-formatted dates."""
    rows = conversation_repo.list_by_user(user_id)
    conversations = []
    for row in rows:
        conv = dict(row)
        conv["created_at"] = conv["created_at"].isoformat()
        conv["updated_at"] = conv["updated_at"].isoformat()
        conversations.append(conv)
    return conversations


def get_with_messages(conversation_id, user_id):
    """Load a conversation and all its messages. Returns (conversation, messages) or (None, None)."""
    conv = conversation_repo.find_by_id_and_user(conversation_id, user_id)
    if conv is None:
        return None, None

    messages = message_repo.get_full_history(conversation_id)
    msg_list = []
    for msg in messages:
        m = dict(msg)
        m["created_at"] = m["created_at"].isoformat()
        msg_list.append(m)

    return dict(conv), msg_list


def delete(conversation_id, user_id):
    """Delete a conversation. Returns True if found and deleted, False if not found."""
    conv = conversation_repo.find_by_id_and_user(conversation_id, user_id)
    if conv is None:
        return False
    conversation_repo.delete(conversation_id)
    return True
