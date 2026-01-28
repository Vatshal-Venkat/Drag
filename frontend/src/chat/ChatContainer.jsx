import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

export default function ChatContainer() {
  return (
    <div style={styles.container}>
      <MessageList />
      <MessageInput />
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
  },
};