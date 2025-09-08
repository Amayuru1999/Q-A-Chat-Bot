import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();

  const isChat = location.pathname === "/chat";
  const isMath = location.pathname === "/math";

  return (
    <header>
      <div className="header-inner" style={{ justifyContent: "space-between" }}>
        <div style={{ display: "grid" }}>
          <div className="title">Learning Assistant</div>
          <div className="sub">RAG • FastAPI • Vite</div>
        </div>

     
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className={`btn ${isChat ? "primary" : ""}`}
            onClick={() => navigate("/chat")}
          >
            Chat
          </button>
          <button
            className={`btn ${isMath ? "primary" : ""}`}
            onClick={() => navigate("/math")}
          >
            Math
          </button>
        </div>
      </div>
    </header>
  );
}
