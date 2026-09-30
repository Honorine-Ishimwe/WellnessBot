"""
Safety module — crisis detection, medical disclaimers, and escalation logic.
Runs as a pre-processing guard before the agent loop.
"""

import re

# ── Crisis keywords and patterns ──────────────────────

_CRISIS_PATTERNS = [
    r"\b(suicid\w*|kill\s*(my)?self|end(ing)?\s*(my)?\s*life|don'?t\s*want\s*to\s*live)\b",
    r"\b(self[- ]?harm\w*|cut(ting)?\s*(my)?self|hurt(ing)?\s*(my)?self)\b",
    r"\b(want\s*to\s*die|rather\s*(be\s*)?dead|no\s*reason\s*to\s*live)\b",
    r"\b(overdose\w*|swallow(ed|ing)?\s*pills)\b",
]

_CRISIS_RE = re.compile("|".join(_CRISIS_PATTERNS), re.IGNORECASE)

# ── Medical diagnosis patterns ────────────────────────

_MEDICAL_PATTERNS = [
    r"\b(diagnos\w*|prescri\w*|what\s*(medication|medicine|drug|pill)s?)\b",
    r"\b(should\s*I\s*take|dosage|side\s*effects?\s*of)\b",
    r"\b(is\s*this\s*(a\s*)?(cancer|infection|disease|disorder))\b",
    r"\b(medical\s*advice|clinical\s*diagnosis|blood\s*test\s*results?)\b",
    r"\b(chest\s*pain|heart\s*attack|stroke\s*symptoms?)\b",
]

_MEDICAL_RE = re.compile("|".join(_MEDICAL_PATTERNS), re.IGNORECASE)


# ── Crisis response ──────────────────────────────────

CRISIS_RESPONSE = (
    "I hear you, and I want you to know that you matter deeply. What you're feeling "
    "right now is real, and you don't have to face it alone. 💙\n\n"
    "Please reach out to someone who can help right now:\n\n"
    "📞 **988 Suicide & Crisis Lifeline** — Call or text **988** (available 24/7)\n"
    "💬 **Crisis Text Line** — Text **HOME** to **741741**\n\n"
    "These services are free, confidential, and available around the clock. "
    "You deserve support, and trained counselors are ready to listen. 💙"
)


# ── Medical disclaimer ───────────────────────────────

MEDICAL_DISCLAIMER = (
    "I appreciate you sharing that with me. I want to be transparent — "
    "I'm a wellness companion, not a licensed medical professional. "
    "I can share general wellness tips, but I'm not able to diagnose conditions, "
    "interpret test results, or recommend specific medications. 💙\n\n"
    "For medical questions, I'd strongly encourage you to consult with your doctor "
    "or a qualified healthcare provider who can give you personalized guidance. "
    "Is there something wellness-related I can help you with instead?"
)


def check_safety(user_message):
    """Check a user message for crisis or medical content.

    Returns:
        (None, None) — message is safe, proceed normally.
        (response_text, "crisis") — crisis detected, return this response immediately.
        (response_text, "medical") — medical question detected, return this response.
    """
    # Crisis detection takes highest priority
    if _CRISIS_RE.search(user_message):
        return CRISIS_RESPONSE, "crisis"

    # Medical diagnosis / prescription detection
    if _MEDICAL_RE.search(user_message):
        return MEDICAL_DISCLAIMER, "medical"

    return None, None
