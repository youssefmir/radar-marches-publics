import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { useTheme } from "../lib/theme";
import { useBase } from "../lib/hooks";
import { dateFr } from "../lib/format";

const REPO = "https://github.com/youssefmir/radar-marches-publics";

export default function Layout() {
  const [theme, toggle] = useTheme();
  const { data } = useBase();
  const loc = useLocation();
  useEffect(() => window.scrollTo(0, 0), [loc.pathname]);
  return (
    <>
      <a href="#contenu" className="skip">Aller au contenu</a>
      <header className="masthead">
        <div className="container">
          <NavLink to="/" className="brand" aria-label="Radar Marchés Publics, accueil">
            <img src={`${import.meta.env.BASE_URL}favicon.svg`} alt="" />
            <b>Radar Marchés Publics</b>
          </NavLink>
          <nav className="nav" aria-label="Navigation principale">
            <NavLink to="/" end>Étude de cas</NavLink>
            <NavLink to="/radar">Radar AO</NavLink>
            <NavLink to="/panorama">Panorama</NavLink>
            <NavLink to="/acheteurs">Acheteurs</NavLink>
            <NavLink to="/methode">Méthode</NavLink>
          </nav>
          <button className="theme-btn" onClick={toggle} aria-label={`Passer au thème ${theme === "dark" ? "clair" : "sombre"}`}>
            {theme === "dark" ? "Thème clair" : "Thème sombre"}
          </button>
        </div>
      </header>
      <div className="dateline" aria-label="Fraîcheur des données">
        <div className="container">
          <span>DECP · version du {data ? dateFr(data.meta.decp.version) : "…"}</span>
          <span>BOAMP · instantané du {data ? dateFr(data.meta.boamp.snapshot_date) : "…"}</span>
          <span>Données ouvertes · Licence Ouverte 2.0</span>
        </div>
      </div>
      <main id="contenu">
        <Outlet />
      </main>
      <footer className="footer">
        <div className="container">
          <span>Projet réalisé par <strong>Youssef Mir</strong> — Business Analyst IA</span>
          <span>
            <a href="https://github.com/youssefmir">github.com/youssefmir</a>
            {"  ·  "}
            <a href={REPO}>Code source du projet</a>
          </span>
        </div>
      </footer>
    </>
  );
}

export { REPO };
