import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Sidebar from "../components/chat/Sidebar";
import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";
import EscalateModal from "../components/tickets/EscalatedModal";
import {
    getSessions,
    createSession,
    getMessages,
    sendMessage,
    deleteSession
} from "../services/chat";

import "./chat.css";

export default function Chat() {
    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showEscalateModal, setShowEscalateModal] = useState(false);

    const navigate = useNavigate();
    const { user, logout } = useAuth();

    useEffect(() => {
        loadSessions();
    }, []);

    useEffect(() => {
        if (!selectedSession) return;

        const interval = setInterval(() => {
            loadMessages(selectedSession);
        }, 2000);

        return () => clearInterval(interval);
    }, [selectedSession]);

    const handleLogout = () => {
        logout();
        navigate("/");
    };

    const loadSessions = async () => {
        try {
            const data = await getSessions();

            setSessions(data);

            if (data.length > 0) {
                loadMessages(data[0]);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleNewChat = async () => {
        try {
            const session = await createSession();

            await loadSessions();

            setSelectedSession(session);
        } catch (err) {
            console.error(err);
        }
    };

    const loadMessages = async (session) => {
        try {
            const data = await getMessages(session.id);

            setMessages(data);
            setSelectedSession(session);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSend = async (text) => {
        if (!selectedSession) return;

        setLoading(true);

        try {
            await sendMessage(
                selectedSession.id,
                text
            );

            await loadMessages(selectedSession);
            await loadSessions();
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteSession = async (sessionId) => {
        try {
            await deleteSession(sessionId);
            await loadSessions();
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="chat-page">

            <Sidebar
                sessions={sessions}
                selectedSession={selectedSession}
                onSelectSession={loadMessages}
                onNewChat={handleNewChat}
                onDelete={handleDeleteSession}
                onLogout={handleLogout}
                user={user}
            />

            <main className="chat-main">

                <header className="chat-header">

    <div className="chat-header-title">

        <div className="brand-mark brand-mark-small">
            H
        </div>

        <div>
            <h1>The Help Desk</h1>

            <p>
                <span className="status-dot" />
                AI Support Assistant
            </p>
        </div>

    </div>

</header>

                <section className="chat-content">

                    <ChatWindow
                        messages={messages}
                        selectedSession={selectedSession}
                        onNewChat={handleNewChat}
                    />

                    <div className="chat-composer-area">

                        {selectedSession && (
                            <div className="escalation-bar">

                                <div className="escalation-copy">

                                    <span className="escalation-icon">
                                        ↗
                                    </span>

                                    <div>
                                        <strong>
                                            Need more help?
                                        </strong>

                                        <span>
                                            Connect with a human support agent
                                        </span>
                                    </div>

                                </div>

                                <button
                                    className="escalation-button"
                                    onClick={() =>
                                        setShowEscalateModal(true)
                                    }
                                >
                                    Escalate to Human
                                </button>

                            </div>
                        )}

                        <ChatInput
                            onSend={handleSend}
                            disabled={loading}
                        />

                        <p className="chat-disclaimer">
                            AI responses may be inaccurate. Verify important policy details.
                        </p>

                    </div>

                </section>

                <EscalateModal
                    open={showEscalateModal}
                    sessionId={selectedSession?.id}
                    onClose={() =>
                        setShowEscalateModal(false)
                    }
                />

            </main>

        </div>
    );
}