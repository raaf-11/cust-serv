const SUGGESTIONS = [
    "How long is the warranty on my laptop?",
    "When will my UPI refund arrive?",
    "My laptop is running slowly. What should I do?",
    "How do I reset my password?",
];

export default function EmptyState({ onSuggestion }) {
    return (
        <div className="empty-state">
            <h2>How can we help?</h2>
            <p>
                Ask about orders, refunds, warranty, your account or a device
                problem. If the answer isn't in our help articles, we'll pass
                you to a member of the support team.
            </p>

            {onSuggestion && (
                <div className="suggestions">
                    {SUGGESTIONS.map((text) => (
                        <button
                            key={text}
                            className="suggestion"
                            onClick={() => onSuggestion(text)}
                        >
                            {text}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
