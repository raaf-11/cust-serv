export default function ChatInput() {

    return (
        <div
            style={{
                borderTop: "1px solid #ddd",
                padding: "20px",
            }}
        >
            <input
                type="text"
                placeholder="Ask anything..."
                style={{
                    width: "100%",
                    padding: "12px",
                }}
            />
        </div>
    );
}