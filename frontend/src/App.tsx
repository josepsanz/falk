import { NavLink, Route, Routes } from "react-router-dom";

import { Backdrop } from "./components/Backdrop";
import { Dashboard } from "./pages/Dashboard";
import { Plugs } from "./pages/Plugs";
import { Settings } from "./pages/Settings";

export function App() {
  return (
    <div className="app">
      <Backdrop />
      <nav className="sidebar">
        <div className="brand">
          <span className="brand__mark">⚡</span>
          <span className="brand__name">Falk</span>
        </div>
        <NavLink to="/" end className="navlink">
          Panell
        </NavLink>
        <NavLink to="/plugs" className="navlink">
          Endolls
        </NavLink>
        <NavLink
          to="/settings"
          className="navlink navlink--cog"
          title="Configuració"
          aria-label="Configuració"
        >
          <span className="cog">⚙</span>
          Configuració
        </NavLink>
      </nav>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/plugs" element={<Plugs />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
