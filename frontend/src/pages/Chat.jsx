import { useEffect, useState } from "react";

import Sidebar from "../components/chat/Sidebar";
import ChatWindow from "../components/chat/ChatWindow";
import ChatInput from "../components/chat/ChatInput";

import {
    getSessions,
    createSession,
} from "../services/chat";

export default function Chat() {

    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async () => {
        try {
            const data = await getSessions();

            setSessions(data);

            if (data.length > 0) {
                setSelectedSession(data[0]);
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
                onSelectSession={setSelectedSession}
                onNewChat={handleNewChat}
            />

            <main
                style={{
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                <ChatWindow />

                <ChatInput />
            </main>
        </div>
    );
}