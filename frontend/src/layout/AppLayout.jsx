import { memo } from "react";
import Sidebar from "../sidebar/Sidebar";
import ChatContainer from "../chat/ChatContainer";
import { useChatStore } from "../store/chatStore";

const MemoChatContainer = memo(ChatContainer);

export default function AppLayout() {
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);
  const toggleSidebar = useChatStore((s) => s.toggleSidebar);

  return (
    <div style={styles.root}>
      {/* LEFT SIDEBAR */}
      <Sidebar />

      {/* FLOATING SIDEBAR HANDLE */}
      {!sidebarOpen && (
        <div
          style={styles.sidebarHandle}
          onClick={toggleSidebar}
        >
          ❯
        </div>
      )}

      {/* MAIN CHAT */}
      <div
        style={{
          ...styles.main,
          marginLeft: sidebarOpen ? 260 : 0,
          marginRight: 0,
        }}
      >
        <div
          style={{
            ...styles.chatShell,
            pointerEvents: "auto",     // 🔑 allow interaction
            zIndex: 1,
          }}
        >
          <MemoChatContainer />
        </div>
      </div>

      {/* 🚫 RIGHT SOURCES PANEL REMOVED FROM RENDER TREE */}
    </div>
  );
}

const styles = {
  root: {
    display: "flex",
    height: "100vh",
    background: "#141414",
    color: "#e6edf3",
    overflow: "hidden",
    position: "relative",
  },

  main: {
    flex: 1,
    height: "100%",
    background: "#141414",
    transition: "margin 0.25s ease",
    position: "relative",
    zIndex: 1,
  },

  chatShell: {
    position: "relative",
    height: "100%",
  },

  sidebarHandle: {
    position: "fixed",
    left: 0,
    top: "50%",
    transform: "translateY(-50%)",
    background: "#020617",
    border: "1px solid #1f2937",
    borderLeft: "none",
    padding: "10px 8px",
    cursor: "pointer",
    borderRadius: "0 6px 6px 0",
    zIndex: 30,
    color: "#67e8f9",
  },

  /* ⬇️ kept intentionally (future feature / no deletion) */
  sourcesPanel: {
    position: "fixed",
    right: 0,
    top: 0,
    width: 360,
    height: "100vh",
    background: "#020617",
    borderLeft: "1px solid #1f2937",
    transition: "transform 0.25s ease",
    zIndex: 20,
    display: "flex",
    flexDirection: "column",
  },

  sourcesHeader: {
    padding: "14px 18px",
    fontSize: 14,
    fontWeight: 600,
    borderBottom: "1px solid #1f2937",
    color: "#67e8f9",
  },

  sourcesBody: {
    flex: 1,
    overflowY: "auto",
    padding: "16px 18px",
  },
};
