import ReactMarkdown from "react-markdown";

export default function MessageBubble({
    message,
    role,
}) {
    const isUser = role === "user";

    return (
        <div className={`message-row ${isUser ? "user-message-row" : "assistant-message-row"}`}>
            {!isUser && (
                <div className="assistant-avatar">
                    S
                </div>
            )}

            <div className={`message-wrapper ${isUser ? "user-message-wrapper" : "assistant-message-wrapper"}`}>
                <div className="message-meta">
                    <span>
                        {isUser ? "You" : "Support Copilot"}
                    </span>
                </div>

                <div className={`message-bubble ${isUser ? "user-message" : "assistant-message"}`}>
                    {isUser ? (
                        <div className="message-text">
                            {message}
                        </div>
                    ) : (
                        <div className="message-markdown">
                            <ReactMarkdown
                                components={{
                                    p: ({ children }) => (
                                        <p>{children}</p>
                                    ),
                                    ul: ({ children }) => (
                                        <ul>{children}</ul>
                                    ),
                                    ol: ({ children }) => (
                                        <ol>{children}</ol>
                                    ),
                                    h1: ({ children }) => (
                                        <h1>{children}</h1>
                                    ),
                                    h2: ({ children }) => (
                                        <h2>{children}</h2>
                                    ),
                                    h3: ({ children }) => (
                                        <h3>{children}</h3>
                                    ),
                                }}
                            >
                                {message}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
