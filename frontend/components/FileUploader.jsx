"use client";

export default function FileUploader() {
  async function upload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const form = new FormData();
    form.append("file", file);

    await fetch("http://127.0.0.1:8000/ingest", {
      method: "POST",
      body: form,
    });

    alert("Document ingested");
  }

  return <input type="file" accept="application/pdf" onChange={upload} />;
}
