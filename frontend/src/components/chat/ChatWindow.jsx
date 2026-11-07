import { useEffect, useRef } from "react";

import EmptyState from "./EmptyState";
import MessageBubble from "./MessageBubble";

const roleOf = (sender) =>
    sender === "USER" ? "user" : sender === "EMPLOYEE" ? "agent" : "assistant";

export default function ChatWindow({
    messages,
    pendingText,
    sending,
    onSuggestion,
}) {
    const endRef = useRef(null);

    const last = messages[messages.length - 1];
    const showPending =
        pendingText &&
        !(last && last.sender === "USER" && last.content === pendingText);

    const count = messages.length + (showPending ? 1 : 0) + (sending ? 1 : 0);

    useEffect(() => {
        endRef.current?.scrollIntoView({ block: "end" });
    }, [count]);

    if (messages.length === 0 && !pendingText) {
        return (
            <div className="chat-window scroll">
                <EmptyState onSuggestion={onSuggestion} />
            </div>
        );
    }

    const lastRole = messages.length ? roleOf(last.sender) : null;

    return (
        <div className="chat-window scroll" aria-live="polite">
            <div className="message-column">
                {messages.map((m, i) => {
                    const role = roleOf(m.sender);
                    const showLabel = i === 0 || roleOf(messages[i - 1].sender) !== role;

                    return (
                        <MessageBubble
                            key={m.id}
                            role={role}
                            message={m.content}
                            time={m.created_at}
                            showLabel={showLabel}
                        />
                    );
                })}

                {showPending && (
                    <MessageBubble
                        role="user"
                        message={pendingText}
                        showLabel={lastRole !== "user"}
                    />
                )}

                {sending && (
                    <div className="message-row assistant">
                        <div className="message-label">Assistant</div>
                        <div className="bubble assistant typing" aria-label="Assistant is typing">
                            <span /><span /><span />
                        </div>
                    </div>
                )}

                <div ref={endRef} />
            </div>
        </div>
    );
}
