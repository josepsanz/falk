import { NavLink, Route, Routes } from "react-router-dom";

import { Backdrop } from "./components/Backdrop";
import { Charts } from "./pages/Charts";
import { Cost } from "./pages/Cost";
import { General } from "./pages/General";
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
          General
        </NavLink>
        <NavLink to="/charts" className="navlink">
          Charts
        </NavLink>
        <NavLink to="/cost" className="navlink">
          Cost
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
          <Route path="/" element={<General />} />
          <Route path="/charts" element={<Charts />} />
          <Route path="/cost" element={<Cost />} />
          <Route path="/plugs" element={<Plugs />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
