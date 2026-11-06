import { TrashIcon } from "../Icons";
import { timeAgo } from "../../utils/time";

export default function SessionItem({
    session,
    selected,
    onClick,
    onDelete,
}) {
    const title = session.title === "New Chat" ? "New conversation" : session.title;

    return (
        <li className={`session-item ${selected ? "selected" : ""}`}>
            <button
                className="session-open"
                onClick={onClick}
                aria-current={selected ? "true" : undefined}
            >
                <span className="session-title">{title}</span>
                <span className="session-time">{timeAgo(session.created_at)}</span>
            </button>

            <button
                className="icon-btn session-delete"
                onClick={(e) => {
                    e.stopPropagation();
                    onDelete(session.id);
                }}
                title="Delete conversation"
                aria-label={`Delete conversation: ${title}`}
            >
                <TrashIcon />
            </button>
        </li>
    );
}
