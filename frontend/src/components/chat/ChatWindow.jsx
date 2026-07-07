import MessageBubble from "./MessageBubble";

export default function ChatWindow({ messages }) {
    return (
        <div
            style={{
                flex: 1,
                overflowY: "auto",
                padding: "20px",
            }}
        >
            {messages.map((message, index) => (
                <MessageBubble
                    key={index}
                    message={message}
                />
            ))}
        </div>
    );
}