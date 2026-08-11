import EmptyState from "./EmptyState";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({
    messages,
}) {

    if (messages.length === 0) {
        return <EmptyState />;
    }

    return (

        <div
            style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                gap: "16px",
                padding: "20px",
                overflowY: "auto",
            }}
        >

            {messages.map((conversation) => (

                <MessageBubble
                    key={conversation.id}
                    role={
                    conversation.sender === "USER"
                    ? "user"
                    : "assistant"
                }
                    message={conversation.content}
            />

        ))}
        </div>

    );

}