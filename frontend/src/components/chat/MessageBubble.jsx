import ReactMarkdown from "react-markdown";

export default function MessageBubble({
    message,
    role,
}) {
    return (
        <div
            style={{
                alignSelf:
                    role === "user"
                        ? "flex-end"
                        : "flex-start",

                padding: "12px",
                borderRadius: "10px",

                background:
                    role === "user"
                        ? "#f5d76e"
                        : "#efefef",

                maxWidth: "70%",
                whiteSpace: "pre-wrap",
                lineHeight: "1.6",
            }}
        >
            {role === "assistant" ? (
                <ReactMarkdown
                    components={{
                        p: ({ children }) => (
                            <p
                                style={{
                                    margin: "0",
                                    textAlign: "left",
                                }}
                            >
                                {children}
                            </p>
                        ),

                        ul: ({ children }) => (
                            <ul
                                style={{
                                    margin: "8px 0",
                                    paddingLeft: "20px",
                                    textAlign: "left",
                                }}
                            >
                                {children}
                            </ul>
                        ),

                        ol: ({ children }) => (
                            <ol
                                style={{
                                    margin: "8px 0",
                                    paddingLeft: "20px",
                                    textAlign: "left",
                                }}
                            >
                                {children}
                            </ol>
                        ),

                        h1: ({ children }) => (
                            <h1
                                style={{
                                    margin: "0 0 12px 0",
                                    textAlign: "left",
                                }}
                            >
                                {children}
                            </h1>
                        ),

                        h2: ({ children }) => (
                            <h2
                                style={{
                                    margin: "0 0 10px 0",
                                    textAlign: "left",
                                }}
                            >
                                {children}
                            </h2>
                        ),

                        h3: ({ children }) => (
                            <h3
                                style={{
                                    margin: "0 0 8px 0",
                                    textAlign: "left",
                                }}
                            >
                                {children}
                            </h3>
                        ),
                    }}
                >
                    {message}
                </ReactMarkdown>
            ) : (
                message
            )}
        </div>
    );
}