import ChatBox from "../components/ChatBox";


export default function UploadPage() {
  return (
    <main style={{ maxWidth: 600, margin: "40px auto" }}>
      <h1>Upload Document</h1>
      <FileUploader />
    </main>
  );
}
