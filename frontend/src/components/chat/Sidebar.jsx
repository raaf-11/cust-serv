import SessionList from "./SessionList";

export default function Sidebar({
    sessions,
    selectedSession,
    onSelectSession,
    onNewChat,
}) {

    return (
        <aside
            style={{
                width: "280px",
                borderRight: "1px solid #ddd",
                display: "flex",
                flexDirection: "column",
                padding: "20px",
                gap: "20px",
            }}
        >

            <button onClick={onNewChat}>
                + New Chat
            </button>

            <SessionList
                sessions={sessions}
                selectedSession={selectedSession}
                onSelectSession={onSelectSession}
            />

            <button
                style={{
                    marginTop: "auto",
                }}
            >
                Logout
            </button>

        </aside>
    );
}