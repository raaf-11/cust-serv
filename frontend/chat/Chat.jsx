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


export default function Chat() {

    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { logout } = useAuth();
    const [showEscalateModal, setShowEscalateModal] = useState(false);
    

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

        } 
        catch (err) {

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

        } 
        catch (err) {

            console.error(err);

        } 
        finally {

            setLoading(false);

        }

    };
    const handleDeleteSession = async (sessionId) => {

        try {

            await deleteSession(sessionId);

            await loadSessions();

        }catch (err) {

            console.error(err);

        }

    };

    return (
        <div
            style={{
                display: "flex",
                height: "100vh",
            }}
        >
            <Sidebar
                sessions={sessions}
                selectedSession={selectedSession}
                onSelectSession={loadMessages}
                onNewChat={handleNewChat}
                onDelete={handleDeleteSession}
                 onLogout={handleLogout}
            />

            <main
                style={{
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                <ChatWindow
                messages={messages}
                 />

                <>
            <ChatInput
                onSend={handleSend}
                disabled={loading}
            />

            {selectedSession && (

            <div
                style={{
                padding: 15,
                display: "flex",
                justifyContent: "center",
            }}
            >

                <button
                    onClick={() =>
                        setShowEscalateModal(true)
                    }
                >
                    Escalate to Human
                </button>

            </div>

            )}

            <EscalateModal

                open={showEscalateModal}

                sessionId={selectedSession?.id}

                onClose={() =>
                    setShowEscalateModal(false)
            }

            />
</>
            </main>
        </div>
    );
}