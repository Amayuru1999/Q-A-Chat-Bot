import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import LandingPage from "./landingpage";
import Chatbot from "./chatbot";
import MathChatbot from "./mathchatbot";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/chat" element={<Chatbot />} />
        <Route path="/math" element={<MathChatbot />} />
      </Routes>
    </Router>
  );
}

export default App;
