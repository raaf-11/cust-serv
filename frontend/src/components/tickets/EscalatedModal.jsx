import { useState } from "react";
import { createTicket } from "../../services/ticket";

export default function EscalateModal({

    sessionId,
    open,
    onClose

}) {

    const [subject, setSubject] = useState("");
    const [description, setDescription] = useState("");

    if (!open) return null;

    const handleSubmit = async () => {

        try {

            await createTicket({

                session_id: sessionId,
                subject,
                description

            });

            alert("Ticket created successfully.");

            setSubject("");
            setDescription("");

            onClose();

        } catch (err) {

            console.error(err);
            alert("Failed to create ticket.");

        }

    };

    return (

        <div
            style={{
                position: "fixed",
                inset: 0,
                background: "rgba(0,0,0,.5)",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
            }}
        >

            <div
                style={{
                    background: "white",
                    padding: 20,
                    width: 450,
                    borderRadius: 10,
                }}
            >

                <h2>Escalate to Human</h2>

                <input

                    placeholder="Subject"

                    value={subject}

                    onChange={(e) =>
                        setSubject(e.target.value)
                    }

                    style={{
                        width: "100%",
                        marginBottom: 10,
                    }}
                />

                <textarea

                    rows={6}

                    placeholder="Describe your issue..."

                    value={description}

                    onChange={(e) =>
                        setDescription(e.target.value)
                    }

                    style={{
                        width: "100%",
                    }}
                />

                <div
                    style={{
                        display: "flex",
                        justifyContent: "flex-end",
                        gap: 10,
                        marginTop: 20,
                    }}
                >

                    <button onClick={onClose}>
                        Cancel
                    </button>

                    <button onClick={handleSubmit}>
                        Create Ticket
                    </button>

                </div>

            </div>

        </div>

    );
}