import EmptyState from "./EmptyState";

export default function ChatWindow() {

    return (
        <div
            style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                padding: "20px",
                overflowY: "auto",
            }}
        >
            <EmptyState />
        </div>
    );
}