import api from "./api";

export async function createTicket(ticket) {

    const response = await api.post(
        "/tickets",
        ticket
    );

    return response.data;
}

export async function getTickets() {

    const response = await api.get(
        "/tickets"
    );

    return response.data;
}