import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { GoogleOAuthProvider } from "@react-oauth/google";

// Wrap App with required providers for testing
const renderApp = () => {
  return render(
    <GoogleOAuthProvider clientId="test-client-id">
      <AuthProvider>
        <App />
      </AuthProvider>
    </GoogleOAuthProvider>
  );
};

describe("App", () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  test("shows auth screen when not logged in", () => {
    renderApp();
    // Should show the sign-in page
    expect(screen.getByText("WellnessBot")).toBeInTheDocument();
    expect(
      screen.getByText("Your safe space for emotional support")
    ).toBeInTheDocument();
  });

  test("has theme toggle button", () => {
    renderApp();
    const themeToggle = screen.getByLabelText(/switch to/i);
    expect(themeToggle).toBeInTheDocument();
  });

  test("shows feature highlights on auth screen", () => {
    renderApp();
    expect(screen.getByText("Talk about how you feel")).toBeInTheDocument();
    expect(
      screen.getByText("Get personalized coping strategies")
    ).toBeInTheDocument();
    expect(screen.getByText("Revisit past conversations")).toBeInTheDocument();
    expect(
      screen.getByText(/Private & secure with auto-delete/)
    ).toBeInTheDocument();
  });
});
