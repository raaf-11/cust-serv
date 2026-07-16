import api from "./api";

export async function getOpenTickets() {

    const response = await api.get(
        "/employee/tickets"
    );

    return response.data;
}

export async function getMyTickets() {

    const response = await api.get(
        "/employee/my-tickets"
    );

    return response.data;
}

export async function acceptTicket(ticketId) {

    const response = await api.patch(
        `/employee/tickets/${ticketId}/accept`
    );

    return response.data;
}

export async function getConversation(ticketId) {

    const response = await api.get(
        `/employee/tickets/${ticketId}/conversation`
    );

    return response.data;
}

export async function sendEmployeeMessage(
    ticketId,
    message
) {

    const response = await api.post(
        `/employee/tickets/${ticketId}/message`,
        {
            message
        }
    );

    return response.data;
}

export async function resolveTicket(ticketId) {

    const response = await api.patch(
        `/employee/tickets/${ticketId}/resolve`
    );

    return response.data;
}