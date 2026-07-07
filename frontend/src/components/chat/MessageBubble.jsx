export default function MessageBubble({
    message,
    role,
}) {

    return (
        <div
            style={{
                alignSelf:
                    role === "user"
                        ? "flex-end"
                        : "flex-start",

                padding: "12px",
                borderRadius: "10px",

                background:
                    role === "user"
                        ? "#f5d76e"
                        : "#efefef",

                maxWidth: "70%",
            }}
        >
            {message}
        </div>
    );
}