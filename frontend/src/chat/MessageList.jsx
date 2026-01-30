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
        padding: "32px 42px",
      }}
      data-chat-stream
    >
      {messages.map((m, i) => (
        <div
          key={i}
          data-role={m.role}
          style={{
            display: "flex",
            flexDirection: "column",
          }}
        >
          <MessageRow
            role={m.role}
            content={m.content}
            timestamp={
              m.timestamp
                ? new Date(m.timestamp).toLocaleTimeString()
                : ""
            }
          />
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
