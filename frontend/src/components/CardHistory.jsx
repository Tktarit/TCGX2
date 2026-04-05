import { useState } from "react";
import AnalysisResult from "./AnalysisResult";
import GradeRecommendation from "./GradeRecommendation";

export default function CardHistory({ items, onDelete }) {
  const [expandedId, setExpandedId] = useState(null);

  if (!items.length) {
    return <p className="empty-state">No analyses yet.</p>;
  }

  return (
    <ul className="card-history">
      {items.map((item) => {
        const isOpen = expandedId === item.id;
        return (
          <li key={item.id} className={`history-item ${isOpen ? "expanded" : ""}`}>
            <button
              className="history-row"
              onClick={() => setExpandedId(isOpen ? null : item.id)}
            >
              <div className="history-grade">Estimated PSA {item.estimated_psa_grade}</div>
              <div className="history-details">
                <span className={`history-verdict ${item.recommend_submit ? "yes" : "no"}`}>
                  {item.recommend_submit ? "Submit" : "Skip"}
                </span>
                <span className="history-score">{item.overall_score.toFixed(2)}/10</span>
                <span className="history-date">
                  {new Date(item.analyzed_at).toLocaleDateString()}
                </span>
              </div>
              <span className="history-chevron">{isOpen ? "▲" : "▼"}</span>
              {onDelete && (
                <button
                  className="history-delete"
                  onClick={(e) => { e.stopPropagation(); onDelete(item.card_id); }}
                >
                  ✕
                </button>
              )}
            </button>

            {isOpen && (
              <div className="history-breakdown">
                {item.card_filename && (
                  <div className="history-original">
                    <img
                      src={`/uploads/${item.card_filename}`}
                      alt="Original card"
                    />
                  </div>
                )}
                <GradeRecommendation result={item} />
                <AnalysisResult result={item} />
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
