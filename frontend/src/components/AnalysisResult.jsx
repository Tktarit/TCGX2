const CATEGORIES = [
  { key: "corner_score",    label: "Corners" },
  { key: "edge_score",      label: "Edges" },
  { key: "surface_score",   label: "Surface" },
  { key: "centering_score", label: "Centering" },
];

// scores are 0–10
function ScoreBar({ score }) {
  const s     = Number(score) || 0;
  const pct   = (s / 10) * 100;
  const color = s >= 8 ? "#4caf50" : s >= 6 ? "#ff9800" : "#f44336";
  return (
    <>
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="score-label">{s.toFixed(1)}</span>
    </>
  );
}

export default function AnalysisResult({ result }) {
  if (!result) return null;
  const overall = Number(result.overall_score) || 0;
  return (
    <div className="analysis-result">
      <h3>Defect Breakdown</h3>
      {CATEGORIES.map(({ key, label }) => (
        <div key={key} className="score-row">
          <span className="score-name">{label}</span>
          <ScoreBar score={result[key]} />
        </div>
      ))}
      <div className="overall-row">
        <span>Overall Score</span>
        <strong>{overall.toFixed(2)} / 10</strong>
      </div>
    </div>
  );
}
