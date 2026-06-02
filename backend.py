import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app)

# ── OpenAI client (reads OPENAI_API_KEY from env automatically) ──
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


@app.post("/chat")
def chat():
    data = request.get_json(force=True) or {}
    user_message = (data.get("message") or "").strip()
    mood = (data.get("mood") or "").strip()
    history = data.get("history") or []

    if not user_message:
        return jsonify({"reply": "I didn't catch that. Could you say it again?"})

    # Build message list with full conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if mood:
        messages.append({
            "role": "system",
            "content": f"The user's current mood: {mood}. Tailor your tone to this."
        })

    # Include conversation history for context (limit to last 20 messages)
    for msg in history[-20:]:
        role = "assistant" if msg.get("sender") == "bot" else "user"
        messages.append({"role": role, "content": msg.get("text", "")})

    # Add current message
    messages.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=messages,
            max_tokens=250,
            temperature=0.9,
            presence_penalty=0.6,
            frequency_penalty=0.5,
        )
        reply = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OpenAI Error] {e}")
        reply = (
            "I'm having a little trouble connecting right now. "
            "Please try again in a moment. 💙"
        )

    return jsonify({"reply": reply})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)