import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import Sidebar from "../components/chat/Sidebar";
import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";
import EscalateModal from "../components/tickets/EscalatedModal";
import { MenuIcon } from "../components/Icons";
import {
    getSessions,
    createSession,
    getMessages,
    sendMessage,
    deleteSession
} from "../services/chat";

import "./chat.css";

const POLL_MS = 2500;

export default function Chat() {
    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [sending, setSending] = useState(false);
    const [pendingText, setPendingText] = useState(null);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [showEscalateModal, setShowEscalateModal] = useState(false);
    const [toast, setToast] = useState("");

    const selectedRef = useRef(null);
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    const selectSession = useCallback((session) => {
        selectedRef.current = session;
        setSelectedSession(session);
    }, []);

    const loadMessages = useCallback(async (session) => {
        if (!session) return;
        try {
            const data = await getMessages(session.id);
            // Ignore late responses for a chat the user has left.
            if (selectedRef.current?.id === session.id) {
                setMessages(data);
            }
        } catch (err) {
            console.error(err);
        }
    }, []);

    const openSession = useCallback((session) => {
        selectSession(session);
        setMessages([]);
        setDrawerOpen(false);
        loadMessages(session);
    }, [loadMessages, selectSession]);

    // Refresh the chat list. Only picks a chat when none is open, so the
    // user is never moved away from the conversation they're in.
    const loadSessions = useCallback(async () => {
        try {
            const data = await getSessions();
            setSessions(data);

            const current = selectedRef.current;
            if (current) {
                const updated = data.find((s) => s.id === current.id);
                if (updated) selectSession(updated);
            } else if (data.length > 0) {
                openSession(data[0]);
            }
        } catch (err) {
            console.error(err);
        }
    }, [openSession, selectSession]);

    useEffect(() => {
        // Initial fetch; state is set after the request resolves.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        loadSessions();
    }, [loadSessions]);

    // Poll for new messages (e.g. replies from a support agent).
    useEffect(() => {
        if (!selectedSession) return;
        const id = setInterval(() => loadMessages(selectedRef.current), POLL_MS);
        return () => clearInterval(id);
    }, [selectedSession, loadMessages]);

    useEffect(() => {
        if (!toast) return;
        const id = setTimeout(() => setToast(""), 4000);
        return () => clearTimeout(id);
    }, [toast]);

    const handleNewChat = async () => {
        try {
            const session = await createSession();
            setSessions((prev) => [session, ...prev]);
            openSession(session);
            return session;
        } catch (err) {
            console.error(err);
            setToast("Couldn't start a new conversation. Try again.");
            return null;
        }
    };

    const handleSend = async (text) => {
        if (sending) return;

        let session = selectedRef.current;
        if (!session) {
            session = await handleNewChat();
            if (!session) return;
        }

        setSending(true);
        setPendingText(text);

        try {
            await sendMessage(session.id, text);
            await loadMessages(session);
            await loadSessions();
        } catch (err) {
            console.error(err);
            setToast(
                err.response?.status === 429
                    ? err.response.data?.detail || "You're sending messages too quickly. Please wait a moment."
                    : "Your message wasn't sent. Check your connection and try again."
            );
        } finally {
            setSending(false);
            setPendingText(null);
        }
    };

    const handleDeleteSession = async (sessionId) => {
        const ok = window.confirm("Delete this conversation? This can't be undone.");
        if (!ok) return;

        try {
            await deleteSession(sessionId);

            if (selectedRef.current?.id === sessionId) {
                selectSession(null);
                setMessages([]);
            }

            await loadSessions();
        } catch (err) {
            console.error(err);
            setToast(
                err.response?.data?.detail ||
                "Couldn't delete this conversation. Try again."
            );
        }
    };

    const handleLogout = () => {
        logout();
        navigate("/");
    };

    const title =
        selectedSession && selectedSession.title !== "New Chat"
            ? selectedSession.title
            : "New conversation";

    return (
        <div className={`chat-page ${drawerOpen ? "drawer-open" : ""}`}>

            <Sidebar
                sessions={sessions}
                selectedSession={selectedSession}
                onSelectSession={openSession}
                onNewChat={handleNewChat}
                onDelete={handleDeleteSession}
                onLogout={handleLogout}
                onClose={() => setDrawerOpen(false)}
                user={user}
            />

            <button
                className="drawer-scrim"
                aria-label="Close conversations"
                tabIndex={drawerOpen ? 0 : -1}
                onClick={() => setDrawerOpen(false)}
            />

            <main className="chat-main grid-paper">

                <header className="chat-header">
                    <button
                        className="icon-btn chat-menu-btn"
                        aria-label="Open conversations"
                        onClick={() => setDrawerOpen(true)}
                    >
                        <MenuIcon />
                    </button>

                    <div className="chat-header-text">
                        <h1 title={title}>{title}</h1>
                        <p>
                            <span className="status-dot" aria-hidden="true" />
                            Support assistant online
                        </p>
                    </div>
                </header>

                <ChatWindow
                    messages={messages}
                    pendingText={pendingText}
                    sending={sending}
                    onSuggestion={handleSend}
                />

                <div className="chat-composer">
                    <ChatInput onSend={handleSend} disabled={sending} />
                    <p className="chat-disclaimer">
                        Answers come from SmartTech help articles. Ask for a person at any time.
                    </p>
                </div>

                {toast && (
                    <div className="toast" role="status">
                        {toast}
                    </div>
                )}

                <EscalateModal
                    open={showEscalateModal}
                    sessionId={selectedSession?.id}
                    onClose={() => setShowEscalateModal(false)}
                />
            </main>
        </div>
    );
}
