import api from "./api";

export const getSessions = async () => {
    const response = await api.get("/sessions/");
    return response.data;
};

export const createSession = async () => {
    const response = await api.post("/sessions/");
    return response.data;
};