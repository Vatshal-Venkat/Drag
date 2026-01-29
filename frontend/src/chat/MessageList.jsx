import { useEffect, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import MessageRow from "./MessageRow";

export default function MessageList() {
  const messages = useChatStore((s) => s.messages);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "24px",
        background: "#020617",
      }}
    >
      {messages.map((m, i) => (
        <MessageRow
          key={i}
          role={m.role}
          content={m.content}
          timestamp={
            m.timestamp
              ? new Date(m.timestamp).toLocaleTimeString()
              : ""
          }
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}