import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function CardUploader({ onUpload, loading }) {
  const [preview, setPreview] = useState(null);

  const onDrop = useCallback(
    (accepted) => {
      const file = accepted[0];
      if (!file) return;
      setPreview(URL.createObjectURL(file));
      onUpload(file);
    },
    [onUpload]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] },
    maxFiles: 1,
    disabled: loading,
  });

  return (
    <div className="uploader-wrapper">
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
        <small>JPG, PNG, WEBP — max 10 MB</small>
      </div>
    </div>
  );
}
