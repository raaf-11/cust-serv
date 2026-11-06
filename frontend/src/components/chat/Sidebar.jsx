import SessionList from "./SessionList";
import { CloseIcon, PlusIcon, SignOutIcon } from "../Icons";

export default function Sidebar({
    sessions,
    selectedSession,
    onSelectSession,
    onNewChat,
    onDelete,
    onLogout,
    onClose,
    user,
}) {
    const name = user?.name || "Customer";

    return (
        <aside className="chat-sidebar" aria-label="Conversations">

            <div className="sidebar-top">
                <div className="brand">
                    <div className="brand-mark">H</div>
                    <div>
                        <div className="brand-name">Help Desk</div>
                        <div className="brand-sub">SmartTech support</div>
                    </div>
                </div>

                <button
                    className="icon-btn sidebar-close"
                    aria-label="Close conversations"
                    onClick={onClose}
                >
                    <CloseIcon />
                </button>
            </div>

            <button className="btn btn-primary new-chat-btn" onClick={onNewChat}>
                <PlusIcon />
                New conversation
            </button>

            <h2 className="sidebar-heading">Recent</h2>

            <div className="sidebar-list scroll">
                {sessions.length > 0 ? (
                    <SessionList
                        sessions={sessions}
                        selectedSession={selectedSession}
                        onSelectSession={onSelectSession}
                        onDelete={onDelete}
                    />
                ) : (
                    <p className="sidebar-empty">
                        Your conversations will appear here.
                    </p>
                )}
            </div>

            <div className="sidebar-footer">
                <div className="avatar">{name.charAt(0).toUpperCase()}</div>
                <div className="sidebar-user">
                    <strong>{name}</strong>
                    <span>{user?.email || "Customer"}</span>
                </div>
                <button
                    className="icon-btn"
                    onClick={onLogout}
                    aria-label="Sign out"
                    title="Sign out"
                >
                    <SignOutIcon />
                </button>
            </div>
        </aside>
    );
}
