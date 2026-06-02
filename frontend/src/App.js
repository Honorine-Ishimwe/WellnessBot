import React from "react";
import "./App.css";
import WelcomeMessage from "./components/welcomeMessage";
import ChatBox from "./components/chatBox";

function App() {
  return (
    <div className="app-root">
      <div className="bubbles">
        <div className="bubble" style={{ left: "10%", animationDuration: "12s", animationDelay: "0s" }} />
        <div className="bubble" style={{ left: "30%", animationDuration: "15s", animationDelay: "2s" }} />
        <div className="bubble" style={{ left: "50%", animationDuration: "10s", animationDelay: "4s" }} />
        <div className="bubble" style={{ left: "70%", animationDuration: "14s", animationDelay: "1s" }} />
        <div className="bubble" style={{ left: "85%", animationDuration: "11s", animationDelay: "3s" }} />
        <div className="bubble" style={{ left: "20%", animationDuration: "16s", animationDelay: "5s" }} />
        <div className="bubble" style={{ left: "60%", animationDuration: "13s", animationDelay: "6s" }} />
      </div>

      <main className="page">
        <section className="left" aria-label="Welcome">
          <WelcomeMessage />
        </section>
        <section className="right" aria-label="Chat">
          <ChatBox />
        </section>
      </main>
    </div>
  );
}

export default App;