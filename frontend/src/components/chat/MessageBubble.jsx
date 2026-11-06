import ReactMarkdown from "react-markdown";

import { clockTime } from "../../utils/time";

const LABELS = {
    user: "You",
    assistant: "Assistant",
    agent: "Support agent",
};

export default function MessageBubble({
    message,
    role,
    time,
    showLabel = true,
}) {
    const isUser = role === "user";
    const when = clockTime(time);

    return (
        <div className={`message-row ${role}`}>
            {showLabel && (
                <div className="message-label">
                    {LABELS[role]}
                    {when && <time>{when}</time>}
                </div>
            )}

            <div className={`bubble ${role}`}>
                {isUser ? (
                    <p className="bubble-text">{message}</p>
                ) : (
                    <div className="markdown">
                        <ReactMarkdown>{message}</ReactMarkdown>
                    </div>
                )}
            </div>
        </div>
    );
}
