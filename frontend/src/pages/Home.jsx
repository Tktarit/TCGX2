import { useState } from "react";
import CardUploader from "../components/CardUploader";
import AnalysisResult from "../components/AnalysisResult";
import GradeRecommendation from "../components/GradeRecommendation";
import { analyzeCard } from "../services/api";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [originalUrl, setOriginalUrl] = useState(null);

  async function handleUpload(file) {
    setLoading(true);
    setError(null);
    setResult(null);
    setOriginalUrl(URL.createObjectURL(file));
    try {
      const data = await analyzeCard(file);
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const status = err.response?.status;
      if (detail) {
        setError(`[${status}] ${detail}`);
      } else if (err.request) {
        setError("Cannot reach server. Is the backend running on port 8000?");
      } else {
        setError(err.message ?? "Unknown error");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h2>Upload a Card</h2>
      <CardUploader onUpload={handleUpload} loading={loading} />

      {loading && (
        <div className="spinner-wrapper">
          <div className="spinner" />
          <span>Uploading...</span>
        </div>
      )}

      {error && <p className="error">{error}</p>}

      {(originalUrl || result) && (
        <div className="image-compare">
          {originalUrl && (
            <div className="image-compare-item">
              <span className="image-compare-label">Original</span>
              <img src={originalUrl} alt="Original card" />
            </div>
          )}
          {result?.cropped_image && (
            <div className="image-compare-item">
              <span className="image-compare-label">Cropped</span>
              <img src={result.cropped_image} alt="Cropped card" />
            </div>
          )}
        </div>
      )}

      {result && (
        <>
          <GradeRecommendation result={result} />
          <AnalysisResult result={result} />
        </>
      )}
    </div>
  );
}
