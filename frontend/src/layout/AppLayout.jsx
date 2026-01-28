import Sidebar from "../sidebar/Sidebar";
import ChatContainer from "../chat/ChatContainer";

export default function AppLayout() {
  return (
    <div style={styles.root}>
      <Sidebar />
      <ChatContainer />
    </div>
  );
}

const styles = {
  root: {
    display: "grid",
    gridTemplateColumns: "260px 1fr",
    height: "100vh",
    background: "#0b0f14",
    color: "#e6edf3",
  },
};