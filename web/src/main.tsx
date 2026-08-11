import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter, Route, Routes } from "react-router-dom";
import "@fontsource/bitter/600.css";
import "@fontsource/bitter/700.css";
import "@fontsource/public-sans/400.css";
import "@fontsource/public-sans/500.css";
import "@fontsource/public-sans/600.css";
import "@fontsource/public-sans/700.css";
import "@fontsource/spline-sans-mono/400.css";
import "@fontsource/spline-sans-mono/500.css";
import "./styles/global.css";
import Layout from "./components/Layout";
import Accueil from "./pages/Accueil";
import Panorama from "./pages/Panorama";
import Radar from "./pages/Radar";
import Acheteurs from "./pages/Acheteurs";
import Acheteur from "./pages/Acheteur";
import Methode from "./pages/Methode";
import Introuvable from "./pages/Introuvable";

// HashRouter : aucune route ne renvoie de 404 sur GitHub Pages (hébergement statique).
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Accueil />} />
          <Route path="panorama" element={<Panorama />} />
          <Route path="radar" element={<Radar />} />
          <Route path="acheteurs" element={<Acheteurs />} />
          <Route path="acheteurs/:id" element={<Acheteur />} />
          <Route path="methode" element={<Methode />} />
          <Route path="*" element={<Introuvable />} />
        </Route>
      </Routes>
    </HashRouter>
  </React.StrictMode>,
);
