import { useState, useRef } from "react";
import { useChatStore } from "../store/chatStore";

export default function FileIngest() {
  const registerDocument = useChatStore(
    (s) => s.registerDocument
  );

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

      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail);

      registerDocument(data.document_id);
      setStatus(`Indexed ${data.chunks ?? "?"} chunks`);
    } catch {
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

      <button onClick={() => fileInputRef.current.click()}>
        {file ? file.name : "Choose File"}
      </button>

      <button onClick={uploadFile} disabled={!file || loading}>
        {loading ? "Uploading…" : "Upload"}
      </button>

      {status && <div>{status}</div>}
    </div>
  );
}
