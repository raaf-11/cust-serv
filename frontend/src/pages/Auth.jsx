import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { login, register } from "../services/auth";
import { useAuth } from "../context/AuthContext";

import "./auth.css";

const homeFor = (role) => (role === "EMPLOYEE" ? "/employee" : "/chat");

function Auth() {
    const [mode, setMode] = useState("login");
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState("");

    const navigate = useNavigate();
    const { login: saveLogin, isAuthenticated, user } = useAuth();

    const isLogin = mode === "login";

    if (isAuthenticated && user) {
        return <Navigate to={homeFor(user.role)} replace />;
    }

    function switchMode(next) {
        setMode(next);
        setError("");
        setNotice("");
    }

    async function handleSubmit(e) {
        e.preventDefault();
        setLoading(true);
        setError("");
        setNotice("");

        try {
            if (isLogin) {
                const response = await login(email, password);

                saveLogin(response.data.access_token, {
                    id: response.data.user_id,
                    name: response.data.name,
                    email: response.data.email,
                    role: response.data.role,
                });

                navigate(homeFor(response.data.role));
            } else {
                await register(name, email, password);
                setPassword("");
                setMode("login");
                setNotice("Account created. Sign in with your email and password.");
            }
        } catch (err) {
            const detail = err.response?.data?.detail;
            setError(
                typeof detail === "string"
                    ? detail
                    : Array.isArray(detail)
                        ? detail.map((d) => d.msg).join(". ")
                        : "Couldn't reach the server. Check that the backend is running and try again."
            );
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="auth-page grid-paper">
            <div className="auth-column">

                <div className="brand auth-brand">
                    <div className="brand-mark">H</div>
                    <div>
                        <div className="brand-name">Help Desk</div>
                        <div className="brand-sub">SmartTech customer support</div>
                    </div>
                </div>

                <div className="auth-card">

                    <div className="auth-tabs" role="tablist" aria-label="Account">
                        <button
                            type="button"
                            role="tab"
                            aria-selected={isLogin}
                            className={isLogin ? "active" : ""}
                            onClick={() => switchMode("login")}
                        >
                            Sign in
                        </button>
                        <button
                            type="button"
                            role="tab"
                            aria-selected={!isLogin}
                            className={!isLogin ? "active" : ""}
                            onClick={() => switchMode("register")}
                        >
                            Create account
                        </button>
                    </div>

                    <div className="auth-heading">
                        <h1>{isLogin ? "Welcome back" : "Create your account"}</h1>
                        <p>
                            {isLogin
                                ? "Sign in to continue your conversations with support."
                                : "Ask about orders, refunds, warranty and more. A person can step in whenever you need one."}
                        </p>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit} noValidate={false}>

                        {!isLogin && (
                            <div className="field">
                                <label htmlFor="name">Full name</label>
                                <input
                                    id="name"
                                    className="input"
                                    autoComplete="name"
                                    required
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                />
                            </div>
                        )}

                        <div className="field">
                            <label htmlFor="email">Email</label>
                            <input
                                id="email"
                                type="email"
                                className="input"
                                autoComplete="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                            />
                        </div>

                        <div className="field">
                            <label htmlFor="password">Password</label>
                            <input
                                id="password"
                                type="password"
                                className="input"
                                autoComplete={isLogin ? "current-password" : "new-password"}
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>

                        {error && (
                            <div className="alert alert-error" role="alert">
                                {error}
                            </div>
                        )}

                        {notice && (
                            <div className="alert alert-success" role="status">
                                {notice}
                            </div>
                        )}

                        <button
                            type="submit"
                            className="btn btn-primary auth-submit"
                            disabled={loading}
                        >
                            {loading
                                ? isLogin ? "Signing in…" : "Creating account…"
                                : isLogin ? "Sign in" : "Create account"}
                        </button>
                    </form>
                </div>

                <p className="auth-footnote">
                    Support agents use the same sign-in and go straight to their ticket queue.
                </p>
            </div>
        </div>
    );
}

export default Auth;
