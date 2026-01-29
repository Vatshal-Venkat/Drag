export default function BlinkingCursor() {
  return (
    <span
      style={{
        display: "inline-block",
        width: "1ch",
        marginLeft: "2px",
        animation: "blink 1s steps(1) infinite",
      }}
    >
      |
      <style>
        {`
          @keyframes blink {
            50% { opacity: 0; }
          }
        `}
      </style>
    </span>
  );
}