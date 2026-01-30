import { useEffect, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import MessageRow from "./MessageRow";

export default function MessageList({ hasMessages }) {
  const messages = useChatStore((s) => s.messages);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <div
      data-chat-stream
      style={styles.stream}
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

const styles = {
  stream: {
    flex: 1,
    overflowY: "auto",          // ✅ scrolling restored
    padding: "36px 48px 180px", // ✅ space for input bar
  },
};
