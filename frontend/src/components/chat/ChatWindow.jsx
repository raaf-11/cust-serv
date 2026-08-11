import EmptyState from "./EmptyState";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({
    messages,
    selectedSession,
    onNewChat,
}) {
    if (!selectedSession && messages.length === 0) {
        return (
            <div className="chat-window">
                <EmptyState onNewChat={onNewChat} />
            </div>
        );
    }

    if (messages.length === 0) {
        return (
            <div className="chat-window">
                <EmptyState
                    onNewChat={onNewChat}
                    title="Start the conversation"
                    description="Ask a question about your account, orders, policies, or support requests."
                />
            </div>
        );
    }

    return (
        <div className="chat-window custom-scrollbar">
            <div className="message-column">
                <div className="conversation-date">
                    Conversation
                </div>

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
        </div>
    );
}
