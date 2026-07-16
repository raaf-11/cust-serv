import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
    getOpenTickets,
    getMyTickets,
    acceptTicket,
    getConversation,
    sendEmployeeMessage,
    resolveTicket,
} from "../services/employee";

export default function EmployeeDashboard() {
    const [openTickets, setOpenTickets] = useState([]);
    const [myTickets, setMyTickets] = useState([]);
    const [selectedTicket, setSelectedTicket] = useState(null);
    const [conversation, setConversation] = useState([]);
    const [message, setMessage] = useState("");

    const navigate = useNavigate();

    const { user, logout } = useAuth();
   ;

   

    useEffect(() => {
        loadDashboard();
    }, []);

    useEffect(() => {

        const interval = setInterval(() => {

            loadDashboard();

        }, 2000);

        return () => clearInterval(interval);

    }, []);

    useEffect(() => {

        if (!selectedTicket) return;

            const interval = setInterval(async () => {

            try {

                const history = await getConversation(
                    selectedTicket.id
                );
                if (history.length !== conversation.length) {setConversation(history);}

            }

            catch (err) {

                console.error(err);

            }

        }, 2000);

        return () => clearInterval(interval);

    }, [selectedTicket]);

    const loadDashboard = async () => {
        try {
            const open = await getOpenTickets();
            const mine = await getMyTickets();

            setOpenTickets(open);
            setMyTickets(mine);
        } catch (err) {
            console.error(err);
        }
    };

    const handleAccept = async (ticketId) => {
        try {
            await acceptTicket(ticketId);
            await loadDashboard();
        } catch (err) {
            console.error(err);
        }
    };

    const handleSelectTicket = async (ticket) => {
        try {
            const history = await getConversation(ticket.id);

            setConversation(history);
            setSelectedTicket(ticket);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSend = async () => {
        if (!message.trim()) return;

        try {
            await sendEmployeeMessage(
                selectedTicket.id,
                message
            );

            const history = await getConversation(
                selectedTicket.id
            );

            setConversation(history);
            setMessage("");
        } catch (err) {
            console.error(err);
        }
    };

    const handleResolve = async () => {
        try {
            await resolveTicket(selectedTicket.id);

            setSelectedTicket(null);
            setConversation([]);

            await loadDashboard();
        } catch (err) {
            console.error(err);
        }
    };

    const handleLogout = () => {
        logout();
        navigate("/");
    };

    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                height: "100vh",
            }}
        >
            {/* HEADER */}
            <div
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "15px 25px",
                    borderBottom: "1px solid lightgray",
                }}
            >
                <h2>Welcome, {user?.name}</h2>

                <button onClick={handleLogout}>
                    Logout
                </button>
            </div>

            {/* MAIN CONTENT */}
            <div
                style={{
                    display: "flex",
                    flex: 1,
                }}
            >
                {/* LEFT PANEL */}
                <div
                    style={{
                        width: 350,
                        borderRight: "1px solid lightgray",
                        overflowY: "auto",
                        padding: 20,
                    }}
                >
                    <h2>Open Tickets</h2>

                    {openTickets.map((ticket) => (
                        <div
                            key={ticket.id}
                            style={{
                                border: "1px solid gray",
                                padding: 10,
                                marginBottom: 10,
                            }}
                        >
                            <strong>{ticket.subject}</strong>

                            <br />

                            {ticket.status}

                            <br />

                            <button
                                onClick={() =>
                                    handleAccept(ticket.id)
                                }
                            >
                                Accept
                            </button>
                        </div>
                    ))}

                    <hr />

                    <h2>My Tickets</h2>

                    {myTickets.map((ticket) => (
                        <div
                            key={ticket.id}
                            style={{
                                border: "1px solid gray",
                                padding: 10,
                                marginBottom: 10,
                                cursor: "pointer",
                            }}
                            onClick={() =>
                                handleSelectTicket(ticket)
                            }
                        >
                            <strong>{ticket.subject}</strong>

                            <br />

                            {ticket.status}
                        </div>
                    ))}
                </div>

                {/* RIGHT PANEL */}
                <div
                    style={{
                        flex: 1,
                        display: "flex",
                        flexDirection: "column",
                    }}
                >
                    <div
                        style={{
                            flex: 1,
                            overflowY: "auto",
                            padding: 20,
                        }}
                    >
                        {conversation.map((msg) => (
                            <div
                                key={msg.id}
                                style={{
                                    marginBottom: 15,
                                }}
                            >
                                <strong>{msg.sender}</strong>

                                <br />

                                {msg.content}
                            </div>
                        ))}
                    </div>

                    {selectedTicket && (
                        <div
                            style={{
                                padding: 20,
                                borderTop:
                                    "1px solid lightgray",
                            }}
                        >
                            <textarea
                                rows={3}
                                value={message}
                                onChange={(e) =>
                                    setMessage(e.target.value)
                                }
                                style={{
                                    width: "100%",
                                }}
                            />

                            <div
                                style={{
                                    display: "flex",
                                    justifyContent:
                                        "space-between",
                                    marginTop: 10,
                                }}
                            >
                                <button
                                    onClick={handleResolve}
                                >
                                    Resolve
                                </button>

                                <button
                                    onClick={handleSend}
                                >
                                    Send
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}