"""
Message repository — data access for the messages table.
"""

from backend.db import query, execute


def get_history(conversation_id):
    """Get all messages for a conversation, ordered by creation time."""
    rows = query(
        """
        SELECT sender, text FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        """,
        (conversation_id,),
        fetchall=True,
    )
    return [dict(m) for m in rows] if rows else []


def get_full_history(conversation_id):
    """Get all messages with timestamps for a conversation."""
    rows = query(
        """
        SELECT sender, text, created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        """,
        (conversation_id,),
        fetchall=True,
    )
    return rows or []


def save(conversation_id, sender, text):
    """Save a message to the database."""
    execute(
        "INSERT INTO messages (conversation_id, sender, text) VALUES (%s, %s, %s)",
        (conversation_id, sender, text),
    )
