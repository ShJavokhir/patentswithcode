// App.jsx
const App = () => {
  const [scale, setScale] = React.useState(1);

  const zoomIn = () => setScale((s) => Math.min(s + 0.2, 5));
  const zoomOut = () => setScale((s) => Math.max(s - 0.2, 0.2));

  return (
    <div
      style={{
        maxWidth: "100%",
        textAlign: "center",
      }}
    >
      <h2 style={{ marginBottom: "16px" }}>Image Zoom Demo</h2>

      <div style={{ marginBottom: "20px" }}>
        <button
          onClick={zoomOut}
          style={{
            marginRight: "12px",
            padding: "8px 16px",
            border: "1px solid #475569",
            borderRadius: "8px",
            background: "#1e293b",
            color: "#e2e8f0",
            cursor: "pointer",
          }}
        >
          Zoom Out
        </button>

        <button
          onClick={zoomIn}
          style={{
            padding: "8px 16px",
            border: "1px solid #475569",
            borderRadius: "8px",
            background: "#1e293b",
            color: "#e2e8f0",
            cursor: "pointer",
          }}
        >
          Zoom In
        </button>
      </div>

      <div
        style={{
          width: "100%",
          overflow: "hidden",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <img
          src="https://picsum.photos/600/400"
          alt="Random placeholder"
          style={{
            transform: `scale(${scale})`,
            transition: "transform 0.3s ease",
            borderRadius: "12px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.35)",
            maxWidth: "100%",
            height: "auto",
          }}
        />
      </div>

      <p style={{ marginTop: "20px", opacity: 0.6 }}>
        Zoom level: {scale.toFixed(1)}x
      </p>
    </div>
  );
};
