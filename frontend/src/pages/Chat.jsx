import { useEffect, useState } from "react";

import { useAuth } from "../context/AuthContext";

import Sidebar from "../components/chat/Sidebar";
import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";

import {
    createSession,
    sendMessage,
} from "../services/chat";

export default function Chat() {
    const { logout } = useAuth();

    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);

    useEffect(() => {
        handleNewChat();
    }, []);

    const handleNewChat = async () => {
        try {
            const session = await createSession();

            setSessionId(sessionId);

            setMessages([]);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSend = async (text) => {
        if (!sessionId) return;

        const userMessage = {
            role: "user",
            content: text,
        };

        setMessages((prev) => [...prev, userMessage]);

        try {
            const response = await sendMessage(
                sessionId,
                text
            );

            const aiMessage = {
                role: "assistant",
                content: response.answer,
            };

            setMessages((prev) => [
                ...prev,
                aiMessage,
            ]);
        } catch (err) {
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
                sessionId={sessionId}
                onNewChat={handleNewChat}
                onLogout={logout}
            />

            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    flex: 1,
                }}
            >
                <ChatWindow messages={messages} />

                <ChatInput onSend={handleSend} />
            </div>
        </div>
    );
}