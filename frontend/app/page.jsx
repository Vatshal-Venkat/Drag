"use client";

import ChatBox from "@/components/ChatBox";

export default function Home() {
  return (
    <main style={{ maxWidth: "800px", margin: "40px auto" }}>
      <h1>AI-DOC RAG Chat</h1>
      <ChatBox />
    </main>
  );
}
