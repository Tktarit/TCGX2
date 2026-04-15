import axios from "axios";

const api = axios.create({ baseURL: "" });

export async function analyzeCard(file, cardNameHint = "", cardSetHint = "") {
  const form = new FormData();
  form.append("file", file);
  if (cardNameHint) form.append("card_name_hint", cardNameHint);
  if (cardSetHint)  form.append("card_set_hint",  cardSetHint);
  const { data } = await api.post("/analyze", form);
  return data;
}


export async function getHistory(skip = 0, limit = 20) {
  const { data } = await api.get("/analysis/history", { params: { skip, limit } });
  return data;
}

export async function deleteHistory(cardId) {
  await api.delete(`/analysis/${cardId}`);
}
