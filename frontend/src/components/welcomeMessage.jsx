import React from "react";
import "./welcomeMessage.css";

export default function WelcomeMessage() {
  return (
    <div className="welcome">
      <div className="welcome-content">
        <h1 className="welcome-title">WellnessBot</h1>
        <p className="welcome-subtitle">
          Your safe space for emotional support
        </p>

        <div className="welcome-features">
          <div className="welcome-feature">
            <span>Talk about how you feel</span>
          </div>
          <div className="welcome-feature">
            <span>Get coping strategies</span>
          </div>
          <div className="welcome-feature">
            <span>Private &amp; judgement-free</span>
          </div>
        </div>

        <p className="welcome-disclaimer">
          Not a substitute for professional mental health care.
          <br />
          If you're in crisis, please reach out to a helpline.
        </p>
      </div>
    </div>
  );
}