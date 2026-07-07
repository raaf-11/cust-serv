export default function Sidebar({
    sessionId,
    onNewChat,
    onLogout,
}) {
    return (
        <div
            style={{
                width: "260px",
                borderRight: "1px solid #ddd",
                display: "flex",
                flexDirection: "column",
                padding: "20px",
                gap: "12px",
            }}
        >
            <button onClick={onNewChat}>
                New Chat
            </button>

            <div>
                <strong>Current Session</strong>

                <p>{sessionId || "None"}</p>
            </div>

            <button onClick={onLogout}>
                Logout
            </button>
        </div>
    );
}