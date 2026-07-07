import { useState } from "react";

export default function ChatInput({ onSend }) {
    const [message, setMessage] = useState("");

    const handleSubmit = (e) => {
        e.preventDefault();

        if (!message.trim()) return;

        onSend(message);

        setMessage("");
    };

    return (
        <form
            onSubmit={handleSubmit}
            style={{
                display: "flex",
                padding: "20px",
                gap: "10px",
            }}
        >
            <input
                type="text"
                placeholder="Type a message..."
                value={message}
                onChange={(e) =>
                    setMessage(e.target.value)
                }
                style={{
                    flex: 1,
                    padding: "10px",
                }}
            />

            <button type="submit">
                Send
            </button>
        </form>
    );
}