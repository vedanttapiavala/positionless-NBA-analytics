export default function SHAPpositionlessScatter() {
  return (
    <section className="w-full my-8">
      <h2 className="text-xl font-semibold mb-4">
        Positionless Index and Injuries
      </h2>

      {/* OUTER CONTAINER */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) 320px",
          gap: "24px",
          alignItems: "start",
          width: "100%",
        }}
      >
        {/* LEFT: chart */}
        <div style={{ minWidth: 0 }}>
          <img
            src="/SHAP Positionless Scatter.svg"
            alt="Scatter Plot showing SHAP Values for Positionless Index"
            style={{
              width: "100%",
              display: "block",
              borderRadius: "8px",
              border: "1px solid #2a2a3e",
            }}
          />
        </div>

        {/* RIGHT: card */}
        <div
          style={{
            border: "1px solid #2a2a3e",
            borderRadius: "12px",
            padding: "16px",
            background: "#12121a",
            boxShadow: "0 1px 3px rgba(0,0,0,0.4)",
            transition: "transform 200ms ease, box-shadow 200ms ease",
            color: "#cccccc",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-4px)";
            e.currentTarget.style.boxShadow =
              "0 10px 20px rgba(0,0,0,0.6)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0px)";
            e.currentTarget.style.boxShadow =
              "0 1px 3px rgba(0,0,0,0.4)";
          }}
        >
          <h3
            style={{
              fontSize: "18px",
              fontWeight: 600,
              marginBottom: "8px",
              color: "#cccccc",
            }}
          >
            Nonlinear relationship between positionless index and injury risk.
          </h3>

          <p
            style={{
              fontSize: "14px",
              color: "#aaaaaa",
              lineHeight: 1.4,
            }}
          >
            The most positionless players tended to have increased injury risk. However, the players 
            with the lowest positionless indices also had increased injury risk. This results in the U-shaped
            curve on the left.
          </p>
        </div>
      </div>
    </section>
  );
}