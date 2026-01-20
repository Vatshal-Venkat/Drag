import { useState } from "react";

export default function FileIngest({ onIngest }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

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

      if (!res.ok) throw new Error("Upload failed");

      const data = await res.json();

      // 🔑 send document_id to parent
      onIngest(data.document_id);

      setStatus(`Ingested ${data.chunks} chunks`);
    } catch (err) {
      console.error(err);
      setStatus("Failed to ingest file");
    } finally {
      setLoading(false);
      setFile(null);
    }
  }

  return (
    <div style={{ border: "1px dashed #aaa", padding: 12, marginBottom: 12 }}>
      <input
        type="file"
        accept=".pdf,.doc,.docx"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button
        onClick={uploadFile}
        disabled={!file || loading}
        style={{ marginLeft: 8 }}
      >
        Upload
      </button>

      {status && (
        <p style={{ marginTop: 8, fontSize: 12, color: "#555" }}>
          {status}
        </p>
      )}
    </div>
  );
}
