export default function EmptyState({
    onNewChat,
    title = "How can we help?",
    description = "Start a new conversation with Support Copilot.",
}) {
    return (
        <div className="empty-state">
            <div className="empty-state-mark">S</div>

            <h2>{title}</h2>

            <p>{description}</p>

            {onNewChat && (
                <button
                    className="empty-state-button"
                    onClick={onNewChat}
                >
                    Start New Conversation
                </button>
            )}
        </div>
    );
}
