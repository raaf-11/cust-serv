
export default function SessionItem({
    session,
    selected,
    onClick,
    onDelete,
}) {
    return (
        <div
            style={{
                display: "flex",
                gap: "8px",
            }}
        >
            <button
                onClick={onClick}
                style={{
                    flex: 1,
                    textAlign: "left",
                    padding: "12px",
                    background: selected ? "#f5d76e" : "white",
                    border: "1px solid #ddd",
                    borderRadius: "8px",
                    cursor: "pointer",
                }}
            >
                {session.title}
            </button>

            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onDelete(session.id);
                }}
            >
                🗑
            </button>
        </div>
    );
}