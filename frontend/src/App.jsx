import { Routes, Route, NavLink } from "react-router-dom";
import Home from "./pages/Home";
import History from "./pages/History";
import logo from "./img/logotcgx.png";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>TCGX2 <img src={logo} alt="logo" style={{ height: "3rem", verticalAlign: "middle" }} /></h1>
        <p>Trading Card PSA Grading Analyzer</p>
        <nav>
          <NavLink to="/" end>Analyze</NavLink>
          <NavLink to="/history">History</NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>
    </div>
  );
}
