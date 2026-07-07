export default function MessageBubble({ message }) {
    return (
        <div
            style={{
                display: "flex",
                justifyContent:
                    message.role === "user"
                        ? "flex-end"
                        : "flex-start",
                marginBottom: "12px",
            }}
        >
            <div
                style={{
                    maxWidth: "70%",
                    padding: "10px 14px",
                    borderRadius: "10px",
                    background:
                        message.role === "user"
                            ? "#f4d35e"
                            : "#f5f5f5",
                }}
            >
                {message.content}
            </div>
        </div>
    );
}