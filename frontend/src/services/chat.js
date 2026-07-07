import api from "./api";

export const createSession = async () => {
    const response = await api.post("/sessions/");
    return response.data;
};

export const sendMessage = async (sessionId, message) => {
    const response = await api.post("/chat/", {
        session_id: sessionId,
        message: message,
    });

    return response.data;
};