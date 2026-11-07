import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";

import { useAuth } from "../context/AuthContext";
import ChatInput from "../components/chat/ChatInput";
import { BackIcon, CheckIcon, SignOutIcon } from "../components/Icons";
import { clockTime, timeAgo } from "../utils/time";
import { fixRupeeSymbol } from "../utils/text";
import {
    getOpenTickets,
    getMyTickets,
    acceptTicket,
    getConversation,
    sendEmployeeMessage,
    resolveTicket,
} from "../services/employee";

import "./employee.css";

const POLL_MS = 3000;

const REASONS = {
    "AI Support Escalation": "Assistant couldn't answer",
    "Customer requested a support agent": "Asked for a person",
};
const reasonFor = (ticket) => REASONS[ticket.subject] || ticket.subject;

const ROLES = {
    USER: { key: "customer", label: "Customer" },
    AI: { key: "assistant", label: "AI assistant" },
    EMPLOYEE: { key: "mine", label: "Support agent" },
};
const roleOf = (sender) => ROLES[sender] || ROLES.AI;

function TicketRow({ ticket, selected, onOpen, action }) {
    return (
        <li className={`ticket ${selected ? "selected" : ""}`}>
            <button className="ticket-open" onClick={() => onOpen(ticket)}>
                <span className="ticket-message">{ticket.description}</span>
                <span className="ticket-meta">
                    <span className="ticket-id">#{ticket.id}</span>
                    <span>{reasonFor(ticket)}</span>
                    <span className="ticket-time">{timeAgo(ticket.created_at)}</span>
                </span>
            </button>
            {action}
        </li>
    );
}

export default function EmployeeDashboard() {
    const [openTickets, setOpenTickets] = useState([]);
    const [myTickets, setMyTickets] = useState([]);
    const [selected, setSelected] = useState(null);
    const [conversation, setConversation] = useState([]);
    const [busy, setBusy] = useState(false);
    const [toast, setToast] = useState("");

    const selectedRef = useRef(null);
    const endRef = useRef(null);
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    const loadDashboard = useCallback(async () => {
        try {
            const [open, mine] = await Promise.all([getOpenTickets(), getMyTickets()]);
            setOpenTickets(open);
            setMyTickets(mine);

            const current = selectedRef.current;
            if (current) {
                const fresh = [...mine, ...open].find((t) => t.id === current.id);
                if (fresh && fresh.status !== current.status) {
                    selectedRef.current = fresh;
                    setSelected(fresh);
                }
            }
        } catch (err) {
            console.error(err);
        }
    }, []);

    const loadConversation = useCallback(async (ticket) => {
        if (!ticket) return;
        try {
            const history = await getConversation(ticket.id);
            if (selectedRef.current?.id === ticket.id) {
                setConversation(history);
            }
        } catch (err) {
            console.error(err);
        }
    }, []);

    useEffect(() => {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        loadDashboard();
        const id = setInterval(loadDashboard, POLL_MS);
        return () => clearInterval(id);
    }, [loadDashboard]);

    useEffect(() => {
        if (!selected) return;
        const id = setInterval(() => loadConversation(selectedRef.current), POLL_MS);
        return () => clearInterval(id);
    }, [selected, loadConversation]);

    useEffect(() => {
        endRef.current?.scrollIntoView({ block: "end" });
    }, [conversation.length, selected?.id]);

    useEffect(() => {
        if (!toast) return;
        const id = setTimeout(() => setToast(""), 4000);
        return () => clearTimeout(id);
    }, [toast]);

    const openTicket = (ticket) => {
        selectedRef.current = ticket;
        setSelected(ticket);
        setConversation([]);
        loadConversation(ticket);
    };

    const closeTicket = () => {
        selectedRef.current = null;
        setSelected(null);
        setConversation([]);
    };

    const handleAccept = async (ticket) => {
        setBusy(true);
        try {
            const accepted = await acceptTicket(ticket.id);
            selectedRef.current = accepted;
            setSelected(accepted);
            loadConversation(accepted);
            await loadDashboard();
        } catch (err) {
            console.error(err);
            setToast("Couldn't accept this ticket. Another agent may have taken it.");
            await loadDashboard();
        } finally {
            setBusy(false);
        }
    };

    const handleSend = async (text) => {
        if (!selected) return;
        setBusy(true);
        try {
            await sendEmployeeMessage(selected.id, text);
            await loadConversation(selected);
        } catch (err) {
            console.error(err);
            setToast("Your reply wasn't sent. Try again.");
        } finally {
            setBusy(false);
        }
    };

    const handleResolve = async () => {
        if (!selected) return;
        setBusy(true);
        try {
            await resolveTicket(selected.id);
            setToast(`Ticket #${selected.id} marked as resolved.`);
            closeTicket();
            await loadDashboard();
        } catch (err) {
            console.error(err);
            setToast("Couldn't resolve this ticket. Try again.");
        } finally {
            setBusy(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate("/");
    };

    const isMine = selected?.status === "IN_PROGRESS";
    const name = user?.name || "Agent";

    return (
        <div className={`emp-page ${selected ? "has-selection" : ""}`}>

            <header className="emp-header">
                <div className="brand">
                    <div className="brand-mark">H</div>
                    <div>
                        <div className="brand-name">Help Desk</div>
                        <div className="brand-sub">Agent workspace</div>
                    </div>
                </div>

                <div className="emp-user">
                    <div className="avatar">{name.charAt(0).toUpperCase()}</div>
                    <span className="emp-user-name">{name}</span>
                    <button
                        className="btn btn-ghost btn-small"
                        onClick={handleLogout}
                    >
                        <SignOutIcon />
                        <span className="emp-signout-label">Sign out</span>
                    </button>
                </div>
            </header>

            <div className="emp-body">

                <aside className="emp-queue scroll" aria-label="Tickets">

                    <section className="queue-section">
                        <h2>
                            Your tickets
                            <span className="count">{myTickets.length}</span>
                        </h2>

                        {myTickets.length === 0 ? (
                            <p className="queue-empty">
                                Tickets you accept show up here.
                            </p>
                        ) : (
                            <ul className="ticket-list">
                                {myTickets.map((t) => (
                                    <TicketRow
                                        key={t.id}
                                        ticket={t}
                                        selected={selected?.id === t.id}
                                        onOpen={openTicket}
                                    />
                                ))}
                            </ul>
                        )}
                    </section>

                    <section className="queue-section">
                        <h2>
                            Waiting for an agent
                            <span className="count">{openTickets.length}</span>
                        </h2>

                        {openTickets.length === 0 ? (
                            <p className="queue-empty">
                                No one is waiting right now.
                            </p>
                        ) : (
                            <ul className="ticket-list">
                                {openTickets.map((t) => (
                                    <TicketRow
                                        key={t.id}
                                        ticket={t}
                                        selected={selected?.id === t.id}
                                        onOpen={openTicket}
                                        action={
                                            <button
                                                className="btn btn-secondary btn-small ticket-accept"
                                                onClick={() => handleAccept(t)}
                                                disabled={busy}
                                            >
                                                Accept
                                            </button>
                                        }
                                    />
                                ))}
                            </ul>
                        )}
                    </section>
                </aside>

                <main className="emp-conversation grid-paper">
                    {!selected ? (
                        <div className="emp-placeholder">
                            <h2>Pick a ticket to start</h2>
                            <p>
                                {myTickets.length > 0
                                    ? "Open one of your tickets to read the conversation and reply to the customer."
                                    : openTickets.length > 0
                                        ? "Accept a waiting ticket to take over the conversation from the assistant."
                                        : "When the assistant hands a customer over, their ticket appears in the queue."}
                            </p>
                        </div>
                    ) : (
                        <>
                            <div className="conv-header">
                                <button
                                    className="icon-btn conv-back"
                                    onClick={closeTicket}
                                    aria-label="Back to tickets"
                                >
                                    <BackIcon />
                                </button>

                                <div className="conv-title">
                                    <h2>Ticket #{selected.id}</h2>
                                    <p>
                                        {reasonFor(selected)}, opened {timeAgo(selected.created_at)}
                                    </p>
                                </div>

                                {isMine ? (
                                    <button
                                        className="btn btn-secondary btn-small"
                                        onClick={handleResolve}
                                        disabled={busy}
                                    >
                                        <CheckIcon />
                                        Mark resolved
                                    </button>
                                ) : (
                                    <button
                                        className="btn btn-primary btn-small"
                                        onClick={() => handleAccept(selected)}
                                        disabled={busy}
                                    >
                                        Accept ticket
                                    </button>
                                )}
                            </div>

                            <div className="conv-messages scroll">
                                <div className="message-column">
                                    {conversation.map((m, i) => {
                                        const role = roleOf(m.sender);
                                        const showLabel =
                                            i === 0 || roleOf(conversation[i - 1].sender).key !== role.key;
                                        const when = clockTime(m.created_at);

                                        return (
                                            <div key={m.id} className={`message-row ${role.key}`}>
                                                {showLabel && (
                                                    <div className="message-label">
                                                        {role.key === "mine" ? "You" : role.label}
                                                        {when && <time>{when}</time>}
                                                    </div>
                                                )}
                                                <div className={`bubble ${role.key}`}>
                                                    {role.key === "assistant" ? (
                                                        <div className="markdown">
                                                            <ReactMarkdown>{fixRupeeSymbol(m.content)}</ReactMarkdown>
                                                        </div>
                                                    ) : (
                                                        <p className="bubble-text">{m.content}</p>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                    <div ref={endRef} />
                                </div>
                            </div>

                            <div className="conv-composer">
                                {isMine ? (
                                    <ChatInput
                                        onSend={handleSend}
                                        disabled={busy}
                                        placeholder="Reply to the customer"
                                    />
                                ) : (
                                    <p className="conv-locked">
                                        Accept this ticket to reply. The customer
                                        sees your messages in their chat.
                                    </p>
                                )}
                            </div>
                        </>
                    )}

                    {toast && <div className="toast" role="status">{toast}</div>}
                </main>
            </div>
        </div>
    );
}
