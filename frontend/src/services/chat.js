import api from "./api";

export const getSessions = async () => {
    const response = await api.get("/sessions/");
    return response.data;
};

export const createSession = async () => {
    const response = await api.post("/sessions/");
    return response.data;
};

export const getMessages = async (sessionId) => {
    const response = await api.get(`/sessions/${sessionId}`);
    return response.data;
};

export const sendMessage = async (sessionId, message) => {
    const response = await api.post("/chat/", {
        session_id: sessionId,
        message: message,
    });


    return response.data;
};

export const deleteSession = async (sessionId) => {
    await api.delete(`/sessions/${sessionId}`);
};
