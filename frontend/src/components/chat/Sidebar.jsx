import SessionList from "./SessionList";

export default function Sidebar({
    sessions,
    selectedSession,
    onSelectSession,
    onNewChat,
    onDelete,
    onLogout,
    user,
}) {
    return (
        <aside className="chat-sidebar">
            <div className="sidebar-brand">
                <div className="brand-mark">S</div>
                <div>
                    <div className="brand-name">SmartTech</div>
                    <div className="brand-subtitle">Support Copilot</div>
                </div>
            </div>

            <button
                className="new-chat-button"
                onClick={onNewChat}
            >
                <span className="new-chat-plus">+</span>
                <span>New conversation</span>
            </button>

            <div className="sidebar-section-label">
                Conversations
            </div>

            <div className="sidebar-session-list custom-scrollbar">
                {sessions.length > 0 ? (
                    <SessionList
                        sessions={sessions}
                        selectedSession={selectedSession}
                        onSelectSession={onSelectSession}
                        onDelete={onDelete}
                    />
                ) : (
                    <div className="sidebar-empty">
                        No conversations yet.
                    </div>
                )}
            </div>

            <div className="sidebar-footer">
                <div className="sidebar-user">
                    <div className="user-avatar">
                        {(user?.name || "C").charAt(0).toUpperCase()}
                    </div>

                    <div className="sidebar-user-info">
                        <strong>{user?.name || "Customer"}</strong>
                        <span>Customer</span>
                    </div>
                </div>

                <button
                    className="logout-button"
                    onClick={onLogout}
                    title="Logout"
                >
                    <span>↪</span>
                    <span>Logout</span>
                </button>
            </div>
        </aside>
    );
}
