export default function GradeRecommendation({ result }) {
  const { estimated_psa_grade, recommend_submit, recommendation_reason } = result;

  return (
    <div className={`recommendation ${recommend_submit ? "recommend-yes" : "recommend-no"}`}>
      <div className="grade-badge">
        <span className="grade-label">Estimated PSA</span>
        <span className="grade-value">{estimated_psa_grade}</span>
      </div>
      <div className="recommendation-body">
        <p className="recommend-verdict">
          {recommend_submit ? "Submit for Grading" : "Not Worth Grading"}
        </p>
        <p className="recommend-reason">{recommendation_reason}</p>
      </div>
    </div>
  );
}
