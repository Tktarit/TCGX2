import { useState, useEffect } from "react";
import CardHistory from "../components/CardHistory";
import { getHistory, deleteHistory } from "../services/api";

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getHistory()
      .then(setItems)
      .catch(() => setError("Failed to load history."))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(cardId) {
    await deleteHistory(cardId);
    setItems((prev) => prev.filter((item) => item.card_id !== cardId));
  }

  return (
    <div className="page">
      <h2>Analysis History</h2>
      {loading && <p className="loading">Loading...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && <CardHistory items={items} onDelete={handleDelete} />}
    </div>
  );
}
