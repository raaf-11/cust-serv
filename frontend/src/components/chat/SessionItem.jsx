export default function SessionItem({
    session,
    selected,
    onClick,
}) {

    return (

        <button
            onClick={onClick}
            style={{
                textAlign: "left",
                padding: "12px",
                background:
                    selected
                        ? "#f5d76e"
                        : "white",

                border: "1px solid #ddd",
                borderRadius: "8px",

                cursor: "pointer",
            }}
        >
            {session.title}
        </button>

    );
}