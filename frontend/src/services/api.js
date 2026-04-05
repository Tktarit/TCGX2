import axios from "axios";

const api = axios.create({ baseURL: "" });

export async function analyzeCard(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/analyze", form);
  return data;
}

export async function uploadCard(file) {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/cards/upload", form);
  return data;
}

export async function runAnalysis(cardId) {
  const { data } = await api.post(`/analysis/${cardId}`);
  return data;
}

export async function getCard(cardId) {
  const { data } = await api.get(`/cards/${cardId}`);
  return data;
}

export async function getHistory(skip = 0, limit = 20) {
  const { data } = await api.get("/analysis/history", { params: { skip, limit } });
  return data;
}

export async function deleteHistory(cardId) {
  await api.delete(`/analysis/${cardId}`);
}
