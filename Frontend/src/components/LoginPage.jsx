/**
 * LoginPage.jsx
 *
 * Viser innlogging og registreringsskjema.
 * Bytter mellom innlogging og registrering via faner.
 * Inkluderer frontend-validering av e-post og passord.
 * Stiler ligger i src/Styles/auth.css
 */

import React, { useState } from "react";
import "../Styles/auth.css";

export default function LoginPage({ onLogin, onRegister, authError, authLoading }) {
    const [isRegistering, setIsRegistering] = useState(false);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [validationError, setValidationError] = useState("");

    // ── Frontend validation ───────────────────────────────
    const validateEmail = (email) => {
        const pattern = /^[\w.-]+@[\w.-]+\.\w{2,}$/;
        return pattern.test(email);
    };

    const validatePassword = (password) => {
        if (!/\d/.test(password))
            return "Passordet må inneholde minst ett tall";
        return null;
    };

    const handleSubmit = async () => {
        setValidationError("");

        if (isRegistering) {
            // Validate name
            if (!name.trim()) {
                setValidationError("Navn er påkrevd");
                return;
            }

            // Validate email
            if (!validateEmail(email)) {
                setValidationError("Ugyldig e-postadresse");
                return;
            }

            // Validate password strength
            const passwordError = validatePassword(password);
            if (passwordError) {
                setValidationError(passwordError);
                return;
            }

            // Validate password confirmation
            if (password !== confirmPassword) {
                setValidationError("Passordene stemmer ikke overens");
                return;
            }

            await onRegister(name, email, password);
        } else {
            if (!email || !password) {
                setValidationError("Fyll inn e-post og passord");
                return;
            }
            await onLogin(email, password);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter") handleSubmit();
    };

    const switchTab = (toRegister) => {
        setIsRegistering(toRegister);
        setName("");
        setEmail("");
        setPassword("");
        setConfirmPassword("");
        setValidationError("");
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

                {/* Bekreft passord — vises kun ved registrering */}
                {isRegistering && (
                    <div className="auth-field">
                        <label className="auth-label">Bekreft passord</label>
                        <input
                            className="auth-input"
                            type="password"
                            placeholder="••••••••"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        {/* Show match indicator */}
                        {confirmPassword && (
                            <div style={{
                                marginTop: "6px",
                                fontSize: "11px",
                                color: password === confirmPassword ? "#22c55e" : "#ef4444",
                                fontWeight: "500"
                            }}>
                                {password === confirmPassword ? "✓ Passordene stemmer" : "✗ Passordene stemmer ikke"}
                            </div>
                        )}
                    </div>
                )}

                {/* Feilmelding — frontend eller backend */}
                {(validationError || authError) && (
                    <div className="auth-error">
                         {validationError || authError}
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