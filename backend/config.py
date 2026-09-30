"""
Configuration constants for WellnessBot.
All environment variables and app-wide settings are centralized here.
"""

import os


# ── OpenAI ────────────────────────────────────────────
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_TOKENS = 500
OPENAI_TEMPERATURE = 0.9
OPENAI_PRESENCE_PENALTY = 0.6
OPENAI_FREQUENCY_PENALTY = 0.5

# ── Chat ──────────────────────────────────────────────
MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_MESSAGES = 20

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

# ── Auth ──────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-to-a-random-secret-string")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# ── Database ──────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
DB_MIN_CONN = 1
DB_MAX_CONN = 10

# ── Cleanup ───────────────────────────────────────────
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))

# ── Knowledge Base / RAG ──────────────────────────────
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
FAISS_INDEX_DIR = os.path.join(KNOWLEDGE_DIR, "index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHUNK_SIZE = 800          # characters per chunk
CHUNK_OVERLAP = 100       # overlap between consecutive chunks
RAG_TOP_K = 3             # number of chunks to retrieve
RAG_SIMILARITY_THRESHOLD = 0.3  # minimum cosine similarity

# ── Agent ─────────────────────────────────────────────
MAX_TOOL_ITERATIONS = 3   # max tool-call hops per user turn
