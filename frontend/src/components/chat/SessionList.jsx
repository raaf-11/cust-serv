import SessionItem from "./SessionItem";

export default function SessionList({
    sessions,
    selectedSession,
    onSelectSession,
    onDelete,
}) {
    return (
        <ul className="session-list">
            {sessions.map((session) => (
                <SessionItem
                    key={session.id}
                    session={session}
                    selected={selectedSession?.id === session.id}
                    onClick={() => onSelectSession(session)}
                    onDelete={onDelete}
                />
            ))}
        </ul>
    );
}
