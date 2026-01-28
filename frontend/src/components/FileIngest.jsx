import { useState, useRef } from "react";

export default function FileIngest({ onIngest }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const fileInputRef = useRef(null);

  async function uploadFile() {
    if (!file) return;

    setLoading(true);
    setStatus("Uploading…");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/ingest/file", {
        method: "POST",
        body: formData,
      });

      console.log("UPLOAD STATUS:", res.status);

      const data = await res.json();
      console.log("UPLOAD RESPONSE:", data);

      if (!res.ok) {
        throw new Error(data?.detail || "Upload failed");
      }

      // protect against missing fields
      if (onIngest && typeof onIngest === "function") {
        onIngest(data.document_id);
      }

      setStatus(`Indexed ${data.chunks ?? "?"} chunks`);
    } catch (err) {
      console.error("UPLOAD ERROR:", err);
      setStatus("Upload failed");
    } finally {
      setLoading(false);
      setFile(null);
    }
  }

  return (
    <div className="ingest-box">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx"
        style={{ display: "none" }}
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button
        className="ingest-select"
        onClick={() => fileInputRef.current.click()}
      >
        {file ? file.name : "Choose File"}
      </button>

      <button
        className="ingest-upload"
        onClick={uploadFile}
        disabled={!file || loading}
      >
        {loading ? "Uploading…" : "Upload"}
      </button>

      {status && <div className="ingest-status">{status}</div>}
    </div>
  );
}