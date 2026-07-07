import SessionItem from "./SessionItem";

export default function SessionList({
    sessions,
    selectedSession,
    onSelectSession,
}) {

    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                gap: "10px",
            }}
        >
            {sessions.map((session) => (

                <SessionItem
                    key={session.id}
                    session={session}
                    selected={
                        selectedSession?.id === session.id
                    }
                    onClick={() =>
                        onSelectSession(session)
                    }
                />

            ))}
        </div>
    );
}