export default function SessionItem({
    session,
    selected,
    onClick,
    onDelete,
}) {
    return (
        <div className={`session-item ${selected ? "selected" : ""}`}>
            <button
                className="session-select-button"
                onClick={onClick}
            >
                <span className="session-icon">○</span>
                <span className="session-title">
                    {session.title}
                </span>
            </button>

            <button
                className="session-delete-button"
                onClick={(e) => {
                    e.stopPropagation();
                    onDelete(session.id);
                }}
                title="Delete conversation"
                aria-label="Delete conversation"
            >
                ×
            </button>
        </div>
    );
}
