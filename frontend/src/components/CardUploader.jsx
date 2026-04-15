import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function CardUploader({ onUpload, loading }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);

  const onDrop = useCallback((accepted) => {
    const f = accepted[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic", ".heif"] },
    maxFiles: 1,
    disabled: loading,
  });

  function handleConfirm() {
    if (file) onUpload(file);
  }

  function handleClear() {
    setFile(null);
    setPreview(null);
  }

  return (
    <div className="uploader-wrapper">
      {!file ? (
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? "active" : ""} ${loading ? "disabled" : ""}`}
        >
          <input {...getInputProps()} />
          {isDragActive ? (
            <p>Drop the card image here...</p>
          ) : (
            <p>Drag & drop a card image, or click to select</p>
          )}
          <small>JPG, PNG, WEBP, AVIF — max 10 MB</small>
        </div>
      ) : (
        <div className="uploader-preview">
          <img src={preview} alt="Selected card" className="uploader-preview-img" />
          <div className="uploader-actions">
            <button className="btn-analyze" onClick={handleConfirm} disabled={loading}>
              {loading ? "Analyzing..." : "Analyze Card"}
            </button>
            <button className="btn-clear" onClick={handleClear} disabled={loading}>
              Change Image
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
