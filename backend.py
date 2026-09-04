"""
WellnessBot — Flask backend with OpenAI GPT, Neon PostgreSQL,
Google OAuth, rate limiting, streaming, and structured logging.
"""

import os
import re
import json
from datetime import datetime, timezone

from typing import Optional, Tuple
from flask import Flask, request, jsonify, Response, stream_with_context, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, AuthenticationError, APIError

from db import init_db, query, execute
from auth import auth_bp, require_auth
from logger import logger, request_logging_middleware

load_dotenv()

app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins != "*":
    allowed_origins = [o.strip() for o in allowed_origins.split(",")]
CORS(app, origins=allowed_origins)

# ── Rate Limiter ──────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per hour"],
    storage_uri="memory://",
)

# ── Logging middleware ────────────────────────────────
request_logging_middleware(app)

# ── Register auth blueprint ──────────────────────────
app.register_blueprint(auth_bp)

# ── OpenAI client ─────────────────────────────────────
client = OpenAI()

SYSTEM_PROMPT = (
    "You are WellnessBot, a warm and creative mental-wellness companion. "
    "You are NOT a licensed therapist or emergency service — you provide general wellness "
    "support only.\n\n"
    "Guidelines for your responses:\n"
    "- Validate the user's feelings genuinely — but NEVER start with 'I'm sorry to hear'. "
    "Use varied, natural openings each time.\n"
    "- Share a helpful tip, but VARY your suggestions widely. Draw from: mindfulness, "
    "gratitude exercises, creative outlets (drawing, music, writing), movement (stretching, "
    "walking), sensory grounding (5-4-3-2-1 technique), positive affirmations, nature, "
    "humor, self-compassion exercises, progressive muscle relaxation, visualization, "
    "aromatherapy, hydration, connecting with someone, or anything creative.\n"
    "- End with a thoughtful follow-up question — vary these too.\n"
    "- CRITICAL: Read the conversation history. Never repeat a tip or exercise you already "
    "suggested. Each response must feel fresh and different.\n"
    "- Keep it concise (under 100 words), conversational, like a caring friend.\n"
    "- Never use numbered lists, bullet points, or bold formatting.\n"
    "- Use occasional emojis naturally.\n"
    "- If the user mentions self-harm, suicidal thoughts, or a crisis, respond with compassion "
    "and strongly encourage them to contact 988 Suicide & Crisis Lifeline or text HOME to 741741.\n"
    "- Match the user's energy — if they're playful, be playful back. If they're heavy, be gentle."
)

MAX_MESSAGE_LENGTH = 2000


# ── Helpers ───────────────────────────────────────────

def sanitize_input(text: str) -> str:
    """Strip HTML tags and limit length."""
    cleaned = re.sub(r"<[^>]+>", "", text)
    return cleaned[:MAX_MESSAGE_LENGTH]


def build_messages(mood: Optional[str], history: list, user_message: str) -> list:
    """Build the OpenAI messages list from conversation context."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if mood:
        messages.append({
            "role": "system",
            "content": f"The user's current mood: {mood}. Tailor your tone to this.",
        })

    # Include conversation history (limit to last 20 messages)
    for msg in history[-20:]:
        role = "assistant" if msg.get("sender") == "bot" else "user"
        messages.append({"role": role, "content": msg.get("text", "")})

    messages.append({"role": "user", "content": user_message})
    return messages


def handle_openai_error(e: Exception) -> Tuple[str, int]:
    """Return a user-friendly error message and HTTP status based on error type."""
    if isinstance(e, RateLimitError):
        logger.warning(f"OpenAI rate limit hit: {e}")
        return (
            "I need a moment to catch my breath. Please try again in a few seconds. 💙",
            429,
        )
    elif isinstance(e, AuthenticationError):
        logger.error(f"OpenAI authentication error: {e}")
        return (
            "I'm having some technical difficulties right now. Please try again later. 💙",
            503,
        )
    elif isinstance(e, APIError):
        logger.error(f"OpenAI API error: {e}")
        return (
            "Something went wrong on my end. Please try again in a moment. 💙",
            502,
        )
    else:
        logger.error(f"Unexpected error: {e}")
        return (
            "I'm having a little trouble connecting right now. Please try again in a moment. 💙",
            500,
        )


# ── Chat endpoint ─────────────────────────────────────

@app.post("/chat")
@require_auth
@limiter.limit("20 per minute")
def chat():
    data = request.get_json(force=True) or {}
    user_message = sanitize_input((data.get("message") or "").strip())
    mood = (data.get("mood") or "").strip() or None
    conversation_id = data.get("conversation_id")

    if not user_message:
        return jsonify({"reply": "I didn't catch that. Could you say it again?"})

    # If no conversation_id, create a new conversation
    if not conversation_id:
        # Use first ~50 chars of message as title
        title = user_message[:50] + ("…" if len(user_message) > 50 else "")
        row = query(
            """
            INSERT INTO conversations (user_id, title, mood)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (g.user_id, title, mood),
            fetchone=True,
        )
        conversation_id = row["id"]

    # Update mood if provided
    if mood:
        execute(
            "UPDATE conversations SET mood = %s WHERE id = %s AND user_id = %s",
            (mood, conversation_id, g.user_id),
        )

    # Load conversation history from DB
    db_messages = query(
        """
        SELECT sender, text FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        """,
        (conversation_id,),
        fetchall=True,
    )
    history = [dict(m) for m in db_messages] if db_messages else []

    # Save the user's message
    execute(
        "INSERT INTO messages (conversation_id, sender, text) VALUES (%s, %s, %s)",
        (conversation_id, "user", user_message),
    )

    # Build messages and call OpenAI
    messages = build_messages(mood, history, user_message)

    try:
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            max_tokens=250,
            temperature=0.9,
            presence_penalty=0.6,
            frequency_penalty=0.5,
        )
        reply = completion.choices[0].message.content.strip()
    except Exception as e:
        reply, status = handle_openai_error(e)
        return jsonify({"reply": reply, "conversation_id": conversation_id}), status

    # Save bot's reply
    execute(
        "INSERT INTO messages (conversation_id, sender, text) VALUES (%s, %s, %s)",
        (conversation_id, "bot", reply),
    )

    return jsonify({"reply": reply, "conversation_id": conversation_id})


# ── Streaming chat endpoint ───────────────────────────

@app.post("/chat/stream")
@require_auth
@limiter.limit("20 per minute")
def chat_stream():
    data = request.get_json(force=True) or {}
    user_message = sanitize_input((data.get("message") or "").strip())
    mood = (data.get("mood") or "").strip() or None
    conversation_id = data.get("conversation_id")

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Create or reuse conversation
    if not conversation_id:
        title = user_message[:50] + ("…" if len(user_message) > 50 else "")
        row = query(
            """
            INSERT INTO conversations (user_id, title, mood)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (g.user_id, title, mood),
            fetchone=True,
        )
        conversation_id = row["id"]

    if mood:
        execute(
            "UPDATE conversations SET mood = %s WHERE id = %s AND user_id = %s",
            (mood, conversation_id, g.user_id),
        )

    # Load history from DB
    db_messages = query(
        """
        SELECT sender, text FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        """,
        (conversation_id,),
        fetchall=True,
    )
    history = [dict(m) for m in db_messages] if db_messages else []

    # Save user message
    execute(
        "INSERT INTO messages (conversation_id, sender, text) VALUES (%s, %s, %s)",
        (conversation_id, "user", user_message),
    )

    messages = build_messages(mood, history, user_message)

    def generate():
        full_reply = []

        # Send conversation_id first
        yield f"data: {json.dumps({'conversation_id': conversation_id})}\n\n"

        try:
            stream = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                max_tokens=250,
                temperature=0.9,
                presence_penalty=0.6,
                frequency_penalty=0.5,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    token = delta.content
                    full_reply.append(token)
                    yield f"data: {json.dumps({'token': token})}\n\n"

        except Exception as e:
            error_msg, _ = handle_openai_error(e)
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            full_reply.append(error_msg)

        # Save the complete reply to DB
        complete_text = "".join(full_reply)
        if complete_text:
            try:
                execute(
                    "INSERT INTO messages (conversation_id, sender, text) VALUES (%s, %s, %s)",
                    (conversation_id, "bot", complete_text),
                )
            except Exception as e:
                logger.error(f"Failed to save bot reply: {e}")

        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Conversation endpoints ────────────────────────────

@app.get("/conversations")
@require_auth
def list_conversations():
    """List all conversations for the authenticated user."""
    rows = query(
        """
        SELECT id, title, mood, created_at, updated_at
        FROM conversations
        WHERE user_id = %s
        ORDER BY updated_at DESC
        """,
        (g.user_id,),
        fetchall=True,
    )
    conversations = []
    for row in (rows or []):
        conv = dict(row)
        conv["created_at"] = conv["created_at"].isoformat()
        conv["updated_at"] = conv["updated_at"].isoformat()
        conversations.append(conv)

    return jsonify({"conversations": conversations})


@app.get("/conversations/<int:conv_id>")
@require_auth
def get_conversation(conv_id):
    """Load all messages for a specific conversation."""
    # Verify ownership
    conv = query(
        "SELECT id, title, mood FROM conversations WHERE id = %s AND user_id = %s",
        (conv_id, g.user_id),
        fetchone=True,
    )
    if conv is None:
        return jsonify({"error": "Conversation not found"}), 404

    messages = query(
        """
        SELECT sender, text, created_at
        FROM messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
        """,
        (conv_id,),
        fetchall=True,
    )

    msg_list = []
    for msg in (messages or []):
        m = dict(msg)
        m["created_at"] = m["created_at"].isoformat()
        msg_list.append(m)

    return jsonify({
        "conversation": dict(conv),
        "messages": msg_list,
    })


@app.delete("/conversations/<int:conv_id>")
@require_auth
def delete_conversation(conv_id):
    """Delete a conversation and all its messages."""
    conv = query(
        "SELECT id FROM conversations WHERE id = %s AND user_id = %s",
        (conv_id, g.user_id),
        fetchone=True,
    )
    if conv is None:
        return jsonify({"error": "Conversation not found"}), 404

    execute("DELETE FROM conversations WHERE id = %s", (conv_id,))
    return jsonify({"success": True})


# ── Health check ──────────────────────────────────────

@app.get("/health")
def health():
    return jsonify({"status": "ok"})


# ── Initialize DB and run ─────────────────────────────

with app.app_context():
    try:
        init_db()
    except Exception as e:
        logger.warning(f"DB init skipped (will retry on first request): {e}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)