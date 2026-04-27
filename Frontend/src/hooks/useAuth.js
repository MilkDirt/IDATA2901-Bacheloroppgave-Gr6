/**
 * useAuth.js
 *
 * Custom hook that handles all authentication logic.
 * Provides login, register, and logout functions,
 * and stores the JWT token in localStorage so the
 * user stays logged in after a page refresh.
 *
 * On startup, verifies the stored token is still valid.
 * If not (e.g. SECRET_KEY changed), clears it and forces re-login.
 */

import { useState, useEffect } from "react";

const API_BASE = "http://127.0.0.1:8000";

export function useAuth() {
    // Initialize token from localStorage so user stays logged in on refresh
    const [token, setToken] = useState(() => localStorage.getItem("token") || null);
    const [user, setUser] = useState(() => {
        const savedUser = localStorage.getItem("user");
        return savedUser ? JSON.parse(savedUser) : null;
    });
    const [authError, setAuthError] = useState("");
    const [authLoading, setAuthLoading] = useState(false);

    // On startup, verify the stored token is still valid.
    // If not (e.g. SECRET_KEY changed), clear it and force re-login.
    useEffect(() => {
        const storedToken = localStorage.getItem("token");
        if (!storedToken) return;

        fetch(`${API_BASE}/conversations/`, {
            headers: { "Authorization": `Bearer ${storedToken}` }
        }).then(res => {
            if (res.status === 401) {
                // Token is invalid or expired — clear and redirect to login
                localStorage.removeItem("token");
                localStorage.removeItem("user");
                setToken(null);
                setUser(null);
            }
        }).catch(() => {
            // Server not reachable — keep token, will fail naturally when used
        });
    }, []);

    /**
     * Register a new user account.
     * On success, saves the token and user info automatically.
     */
    const register = async (name, email, password) => {
        setAuthLoading(true);
        setAuthError("");

        try {
            const response = await fetch(`${API_BASE}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                setAuthError(data.detail || "Registration failed");
                return false;
            }

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("user", JSON.stringify({ name: data.user_name }));
            setToken(data.access_token);
            setUser({ name: data.user_name });
            return true;

        } catch (error) {
            setAuthError("Could not connect to server");
            return false;
        } finally {
            setAuthLoading(false);
        }
    };

    /**
     * Log in with email and password.
     * On success, saves the token and user info.
     */
    const login = async (email, password) => {
        setAuthLoading(true);
        setAuthError("");

        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                setAuthError(data.detail || "Invalid email or password");
                return false;
            }

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("user", JSON.stringify({ name: data.user_name }));
            setToken(data.access_token);
            setUser({ name: data.user_name });
            return true;

        } catch (error) {
            setAuthError("Could not connect to server");
            return false;
        } finally {
            setAuthLoading(false);
        }
    };

    /**
     * Log out the current user.
     * Clears token and user info from localStorage and state.
     */
    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setToken(null);
        setUser(null);
    };

    return {
        token,
        user,
        authError,
        authLoading,
        login,
        register,
        logout,
        isLoggedIn: !!token,
    };
}