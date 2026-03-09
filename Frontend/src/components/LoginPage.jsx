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

                {/* Faner */}
                <div className="auth-tabs">
                    <button
                        className={`auth-tab ${!isRegistering ? "active" : ""}`}
                        onClick={() => switchTab(false)}
                    >
                        Logg inn
                    </button>
                    <button
                        className={`auth-tab ${isRegistering ? "active" : ""}`}
                        onClick={() => switchTab(true)}
                    >
                        Registrer
                    </button>
                </div>

                {/* Overskrift */}
                <h2 className="auth-heading">
                    {isRegistering ? "Opprett konto" : "Velkommen"}
                </h2>
                <p className="auth-subheading">
                    {isRegistering
                        ? "Registrer deg for å bruke informasjonshentingssystemet"
                        : "Logg inn for å få tilgang til samtalene dine"}
                </p>

                {/* Navn — vises kun ved registrering */}
                {isRegistering && (
                    <div className="auth-field">
                        <label className="auth-label">Fullt navn</label>
                        <input
                            className="auth-input"
                            type="text"
                            placeholder="Ditt navn"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                    </div>
                )}

                {/* E-post */}
                <div className="auth-field">
                    <label className="auth-label">E-post</label>
                    <input
                        className="auth-input"
                        type="email"
                        placeholder="deg@eksempel.no"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                {/* Passord */}
                <div className="auth-field">
                    <label className="auth-label">Passord</label>
                    <input
                        className="auth-input"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                {/* Feilmelding fra backend */}
                {authError && (
                    <div className="auth-error">
                         {authError}
                    </div>
                )}

                {/* Send-knapp */}
                <button
                    className="auth-button"
                    onClick={handleSubmit}
                    disabled={authLoading}
                >
                    {authLoading
                        ? "Vennligst vent..."
                        : isRegistering
                            ? "Opprett konto"
                            : "Logg inn"}
                </button>

            </div>
        </div>
    );
}