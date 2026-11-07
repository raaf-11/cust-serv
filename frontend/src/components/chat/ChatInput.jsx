import { useRef, useState } from "react";

import { SendIcon } from "../Icons";

const MAX_HEIGHT = 160;
const MAX_LENGTH = 2000;

export default function ChatInput({
    onSend,
    disabled = false,
    placeholder = "Type your question",
}) {
    const [message, setMessage] = useState("");
    const ref = useRef(null);

    const resize = () => {
        const el = ref.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
    };

    const submit = () => {
        const text = message.trim();
        if (!text || disabled) return;
        onSend(text);
        setMessage("");
        requestAnimationFrame(resize);
    };

    return (
        <form
            className="composer"
            onSubmit={(e) => {
                e.preventDefault();
                submit();
            }}
        >
            <label htmlFor="chat-message" className="visually-hidden">
                Message
            </label>
            <textarea
                id="chat-message"
                ref={ref}
                rows={1}
                maxLength={MAX_LENGTH}
                placeholder={placeholder}
                value={message}
                onChange={(e) => {
                    setMessage(e.target.value);
                    resize();
                }}
                onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                        e.preventDefault();
                        submit();
                    }
                }}
            />
            <button
                type="submit"
                className="composer-send"
                disabled={disabled || !message.trim()}
                aria-label="Send message"
                title="Send"
            >
                <SendIcon />
            </button>
        </form>
    );
}
