# 🧘 WellnessBot

A compassionate AI-powered wellness chatbot that provides emotional support, coping strategies, and a safe space for mental well-being.

Built with **React** (frontend) and **Flask + OpenAI GPT** (backend).

![WellnessBot](https://img.shields.io/badge/AI-WellnessBot-blue?style=for-the-badge)

---

## ✨ Features

- 💬 Real-time chat interface with a warm, supportive AI
- 🧠 GPT-powered responses with a wellness-focused system prompt
- 🎨 Calming UI with animated bubble backgrounds
- 🔒 Environment-based API key management (never committed)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Node.js 18+**
- An **OpenAI API key** ([get one here](https://platform.openai.com/api-keys))

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/WellnessBot.git
cd WellnessBot
```

### 2. Set up the backend

```bash
# Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and paste your OpenAI API key
```

### 3. Set up the frontend

```bash
cd frontend
npm install
```

### 4. Run the app

Start the **backend** (from project root):

```bash
python backend.py
```

Start the **frontend** (from `frontend/`):

```bash
cd frontend
npm start
```

The app will open at [http://localhost:3000](http://localhost:3000) with the backend API on port 5000.

---

## 🗂️ Project Structure

```
WellnessBot/
├── backend.py          # Flask API with OpenAI GPT integration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── .gitignore
├── README.md
└── frontend/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── App.js          # Main layout
    │   ├── App.css         # Global styles & animations
    │   ├── index.js        # React entry point
    │   └── components/
    │       ├── chatBox.jsx         # Chat interface
    │       └── welcomeMessage.jsx  # Welcome panel
    └── package.json
```

---

## ⚙️ Environment Variables

| Variable         | Description                          | Default          |
| ---------------- | ------------------------------------ | ---------------- |
| `OPENAI_API_KEY` | Your OpenAI API key                  | *(required)*     |
| `OPENAI_MODEL`   | GPT model to use                     | `gpt-3.5-turbo`  |
| `FLASK_APP`      | Flask entry point                    | `backend.py`     |
| `FLASK_RUN_PORT` | Port for the Flask server            | `5000`           |

---

## ⚠️ Disclaimer

WellnessBot is **not** a substitute for professional mental health care. If you or someone you know is in crisis, please contact a licensed therapist or reach out to a crisis helpline.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).