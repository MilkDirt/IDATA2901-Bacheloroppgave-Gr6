/**
 * LoginPage.jsx
 *
 * Displays a login and register form.
 * Switches between login and register mode using tabs.
 * Styles are in src/Styles/auth.css
 */

import React, { useState } from "react";
import "../Styles/auth.css";

export default function LoginPage({ onLogin, onRegister, authError, authLoading }) {
    const [isRegistering, setIsRegistering] = useState(false);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleSubmit = async () => {
        if (isRegistering) {
            await onRegister(name, email, password);
        } else {
            await onLogin(email, password);
        }
    };

    // Allow pressing Enter to submit
    const handleKeyDown = (e) => {
        if (e.key === "Enter") handleSubmit();
    };

    const switchTab = (toRegister) => {
        setIsRegistering(toRegister);
        setName("");
        setEmail("");
        setPassword("");
    };

    return (
        <div className="auth-wrapper">
            <div className="auth-card">


                {/* Tabs */}
                <div className="auth-tabs">
                    <button
                        className={`auth-tab ${!isRegistering ? "active" : ""}`}
                        onClick={() => switchTab(false)}
                    >
                        Log in
                    </button>
                    <button
                        className={`auth-tab ${isRegistering ? "active" : ""}`}
                        onClick={() => switchTab(true)}
                    >
                        Register
                    </button>
                </div>

                {/* Heading */}
                <h2 className="auth-heading">
                    {isRegistering ? "Create an account" : "Welcome"}
                </h2>
                <p className="auth-subheading">
                    {isRegistering
                        ? "Register to start using the chat informasjonshenting"
                        : "Log in to access your conversations"}
                </p>

                {/* Name field — only shown when registering */}
                {isRegistering && (
                    <div className="auth-field">
                        <label className="auth-label">Full name</label>
                        <input
                            className="auth-input"
                            type="text"
                            placeholder="Your name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                    </div>
                )}

                {/* Email */}
                <div className="auth-field">
                    <label className="auth-label">Email</label>
                    <input
                        className="auth-input"
                        type="email"
                        placeholder="you@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                {/* Password */}
                <div className="auth-field">
                    <label className="auth-label">Password</label>
                    <input
                        className="auth-input"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                {/* Error message from backend */}
                {authError && (
                    <div className="auth-error">
                         {authError}
                    </div>
                )}

                {/* Submit button */}
                <button
                    className="auth-button"
                    onClick={handleSubmit}
                    disabled={authLoading}
                >
                    {authLoading
                        ? "Please wait..."
                        : isRegistering
                            ? "Create account"
                            : "Log in"}
                </button>

            </div>
        </div>
    );
}