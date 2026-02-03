import { useEffect, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import MessageRow from "./MessageRow";

export default function MessageList({ hasMessages }) {
  const messages = useChatStore((s) => s.messages);
  const bottomRef = useRef(null);
  const containerRef = useRef(null); // ✅ NEW

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  // ✅ NEW: expose scroll container for future features
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.dataset.scrollReady = "true";
    }
  }, []);

  return (
    <div
      ref={containerRef}                 // ✅ NEW
      data-chat-stream
      style={styles.stream}
    >
      {messages.map((m, i) => (
        <MessageRow
          key={i}
          role={m.role}
          content={m.content}
          citations={m.citations || []}
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
    overflowY: "auto",
    padding: "36px 48px 180px",
    pointerEvents: "auto",

    // ✅ NEW: smoother scrolling & modern feel
    scrollBehavior: "smooth",
    scrollbarWidth: "thin",
  },
};
