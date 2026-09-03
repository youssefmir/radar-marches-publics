import { useEffect, useMemo, useState } from "react";
import AvisCard from "../components/AvisCard";
import FranceMap from "../components/FranceMap";
import { Reveal } from "../components/Motion";
import { ScoreLegend } from "../components/ScoreBar";
import { fetchJson } from "../lib/data";
import { dateFr, euros } from "../lib/format";
import { useAsync, useBase, useRegionOf } from "../lib/hooks";
import type { Profil, RadarIndex, RadarRun } from "../lib/radar";

function useApi(): boolean {
  const [ok, setOk] = useState(false);
  useEffect(() => {
    // L'application locale (FastAPI) injecte <meta name="radar-api"> dans la page qu'elle sert ;
    // la démo statique ne l'a pas : aucune requête n'est alors émise.
    const meta = document.querySelector('meta[name="radar-api"]');
    if (!meta) return;
    fetch("/api/health").then((r) => r.ok && r.headers.get("content-type")?.includes("json") && setOk(true)).catch(() => {});
  }, []);
  return ok;
}

export default function Radar() {
  const { data: base } = useBase();
  const regionOf = useRegionOf(base?.dims);
  const idx = useAsync<RadarIndex>(() => fetchJson("radar/index.json")).data;
  const [pid, setPid] = useState("ardoise-batiment");
  const [custom, setCustom] = useState<RadarRun | null>(null);
  const run = useAsync<RadarRun>(() => fetchJson(`radar/${pid}.json`), [pid]).data;
  const api = useApi();
  const current = pid === "personnalise" ? custom : run;

  const balises = useMemo(() => {
    const n = new Map<string, number>();
    for (const r of current?.resultats ?? []) for (const d of r.departements.slice(0, 3)) n.set(d, (n.get(d) ?? 0) + 1);
    return [...n.entries()].map(([dep, k]) => ({ dep, n: k, label: `${k} avis du classement dans le département ${dep}` }));
  }, [current]);

  if (!idx || !base) return <div className="container rubrique"><p className="muted">Chargement…</p></div>;
  const p = current?.profil;

  return (
    <div className="container">
      <section className="rubrique" style={{ marginTop: 28 }}>
        <header>
          <div>
            <div className="kicker">Radar AO · instantané BOAMP du {dateFr(idx.snapshot_date)}</div>
            <h1>Les appels d'offres ouverts, classés pour une entreprise</h1>
          </div>
          <p>
            {idx.nb_avis.toLocaleString("fr-FR")} avis de marché ouverts au {dateFr(idx.snapshot_date)}, classés par un score
            hybride expliqué : pertinence du texte et des codes CPV, territoire, taille, puis concurrence observée chez
            l'acheteur dans l'historique des attributions (DECP).
          </p>
        </header>
        <div className="profils" role="group" aria-label="Profil d'entreprise">
          {idx.profils.map((pr) => (
            <button key={pr.id} aria-pressed={pid === pr.id} onClick={() => setPid(pr.id)}>
              <span className="tag fictif">Profil fictif</span>
              <b style={{ marginTop: 6 }}>{pr.nom}</b>
              <span className="small muted">{pr.secteur} · {pr.effectif} salariés · {pr.ville}</span>
            </button>
          ))}
          {api && (
            <button aria-pressed={pid === "personnalise"} onClick={() => setPid("personnalise")}>
              <span className="tag beacon">Application locale</span>
              <b style={{ marginTop: 6 }}>Mon entreprise</b>
              <span className="small muted">Profil personnalisé, calcul en direct</span>
            </button>
          )}
        </div>
        {pid === "personnalise" && <ProfilForm onResult={setCustom} />}
      </section>

      {p && current && (
        <section className="rubrique">
          <div className="cols cols-main">
            <div>
              <header style={{ marginBottom: 8 }}>
                <div className="kicker">Classement · 30 premiers avis</div>
                <h2>{p.nom}</h2>
              </header>
              <ScoreLegend />
              {current.resultats.map((r, i) => (
                <Reveal key={r.idweb} delay={Math.min(i, 6) * 0.06}>
                  <AvisCard r={r} rang={i + 1} snapshot={current.snapshot_date} delay={0.15 + Math.min(i, 6) * 0.06} api={api} />
                </Reveal>
              ))}
            </div>
            <aside style={{ position: "relative" }}>
              <div style={{ position: "sticky", top: 90 }}>
                <div className="cartouche" style={{ marginTop: 10 }}>
                  <span className="cartouche-title">Profil</span>
                  {p.fictif && <p className="small" style={{ marginTop: 0 }}><span className="tag fictif">Fictif</span> Entreprise inventée pour la démonstration.</p>}
                  <p className="small">{p.description}</p>
                  <dl className="meta">
                    <dt>CPV</dt><dd className="mono small">{p.cpv.join(" ")}</dd>
                    <dt>Territoire</dt><dd className="mono small">{p.departements.join(" ")}</dd>
                    <dt>Montant</dt><dd>{euros(p.montant_min)} – {euros(p.montant_max)}</dd>
                  </dl>
                </div>
                <div className="panel" style={{ marginTop: 22 }}>
                  <h3>Où sont les avis classés</h3>
                  <FranceMap carte={base.carte} values={{}} regionOf={regionOf} format={(x) => String(x)}
                    label={`Carte des départements des avis classés pour ${p.nom}`} balises={balises} />
                  <p className="source">Balises : départements de réalisation des 30 avis (3 premiers départements de chaque avis).</p>
                </div>
              </div>
            </aside>
          </div>
        </section>
      )}
    </div>
  );
}

function ProfilForm({ onResult }: { onResult: (r: RadarRun) => void }) {
  const [form, setForm] = useState<Profil>({
    id: "personnalise", nom: "Mon entreprise", fictif: false, description: "", cpv: [], departements: [], montant_min: null, montant_max: null,
  });
  const [etat, setEtat] = useState<string | null>(null);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEtat("Calcul en cours…");
    const res = await fetch("/api/radar", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
    if (!res.ok) return setEtat("Erreur de l'API locale");
    onResult(await res.json());
    setEtat(null);
  };
  const rafraichir = async () => {
    setEtat("Téléchargement des avis ouverts…");
    await fetch("/api/boamp/refresh", { method: "POST" });
    const poll = window.setInterval(async () => {
      const st = await (await fetch("/api/boamp/status")).json();
      if (st.etat === "terminé") { window.clearInterval(poll); setEtat(`Instantané du ${st.snapshot_date} : ${st.avis} avis ouverts. Relancez le classement.`); }
      else if (st.etat === "échec") { window.clearInterval(poll); setEtat(`Échec du rafraîchissement : ${st.erreur}`); }
      else setEtat(st.etat === "indexation" ? "Indexation (embeddings) en cours, quelques minutes…" : "Téléchargement des avis ouverts…");
    }, 3000);
  };
  const list = (s: string) => s.split(/[\s,;]+/).filter(Boolean);
  return (
    <form onSubmit={submit} className="filters" style={{ marginTop: 18 }}>
      <div className="field" style={{ flex: "2 1 100%" }}>
        <label htmlFor="p-desc">Activité de l'entreprise (texte libre)</label>
        <textarea id="p-desc" required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </div>
      <div className="field"><label htmlFor="p-cpv">Codes CPV (8 chiffres)</label>
        <input id="p-cpv" type="text" placeholder="72000000 72316000" onChange={(e) => setForm({ ...form, cpv: list(e.target.value) })} /></div>
      <div className="field"><label htmlFor="p-dep">Départements</label>
        <input id="p-dep" type="text" placeholder="69 38 42" onChange={(e) => setForm({ ...form, departements: list(e.target.value) })} /></div>
      <div className="field"><label htmlFor="p-min">Montant min (€)</label>
        <input id="p-min" type="number" min={0} onChange={(e) => setForm({ ...form, montant_min: e.target.value ? Number(e.target.value) : null })} /></div>
      <div className="field"><label htmlFor="p-max">Montant max (€)</label>
        <input id="p-max" type="number" min={0} onChange={(e) => setForm({ ...form, montant_max: e.target.value ? Number(e.target.value) : null })} /></div>
      <button className="btn beacon" type="submit">Classer les avis</button>
      <button className="btn ghost" type="button" onClick={rafraichir}>Rafraîchir le BOAMP</button>
      {etat && <span className="small muted" role="status">{etat}</span>}
    </form>
  );
}
