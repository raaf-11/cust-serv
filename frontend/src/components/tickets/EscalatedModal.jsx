import { useState } from "react";

import { createTicket } from "../../services/ticket";

export default function EscalateModal({
    sessionId,
    open,
    onClose
}) {
    const [subject, setSubject] = useState("");
    const [description, setDescription] = useState("");
    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);

    if (!open) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");

        try {
            await createTicket({
                session_id: sessionId,
                subject,
                description
            });
            setSubject("");
            setDescription("");
            onClose();
        } catch (err) {
            console.error(err);
            const detail = err.response?.data?.detail;
            setError(
                typeof detail === "string"
                    ? detail
                    : "Couldn't create the ticket. Subject needs 3+ characters and the description 10+."
            );
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <form
                className="modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="escalate-title"
                onClick={(e) => e.stopPropagation()}
                onSubmit={handleSubmit}
            >
                <div>
                    <h2 id="escalate-title">Talk to a support agent</h2>
                    <p>We'll open a ticket and an agent will reply in this conversation.</p>
                </div>

                <div className="field">
                    <label htmlFor="ticket-subject">Subject</label>
                    <input
                        id="ticket-subject"
                        className="input"
                        required
                        minLength={3}
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                    />
                </div>

                <div className="field">
                    <label htmlFor="ticket-description">What do you need help with?</label>
                    <textarea
                        id="ticket-description"
                        className="textarea"
                        rows={5}
                        required
                        minLength={10}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                    />
                </div>

                {error && <div className="alert alert-error">{error}</div>}

                <div className="modal-actions">
                    <button type="button" className="btn btn-ghost" onClick={onClose}>
                        Cancel
                    </button>
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                        {saving ? "Creating ticket…" : "Create ticket"}
                    </button>
                </div>
            </form>
        </div>
    );
}
