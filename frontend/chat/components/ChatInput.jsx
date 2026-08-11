import { useState } from "react";

export default function ChatInput({
    onSend,
    disabled = false,
}) {

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
                borderTop: "1px solid #ddd",
                padding: "20px",
                display: "flex",
                gap: "10px",
            }}
        >

            <input
                type="text"
                placeholder="Ask anything..."
                value={message}
                disabled={disabled}
                onChange={(e) =>
                    setMessage(e.target.value)
                }
                style={{
                    flex: 1,
                    padding: "12px",
                }}
            />

            <button
                type="submit"
                disabled={disabled}
            >
                Send
            </button>

        </form>

    );

}