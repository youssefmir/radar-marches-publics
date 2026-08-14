import { useState } from "react";
import ScoreBar from "./ScoreBar";
import { dateFr, euros, decimal, pct, entier } from "../lib/format";
import { joursRestants, LIBELLES, type Resultat } from "../lib/radar";

const VERDICT: Record<string, string> = { go: "ok", "à étudier": "warn", "no-go probable": "risk" };
const SYMB: Record<string, string> = { ok: "✓", attention: "!", risque: "×", info: "i", inconnu: "?" };

export default function AvisCard({ r, rang, snapshot, delay = 0, api }: {
  r: Resultat; rang: number; snapshot: string; delay?: number; api?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [resume, setResume] = useState<{ texte?: string; erreur?: string; modele?: string } | null>(null);
  const h = r.historique;
  const j = joursRestants(r.date_limite, snapshot);
  const demanderResume = async () => {
    setResume({});
    try {
      const res = await fetch("/api/resume", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ idweb: r.idweb }) });
      const body = await res.json();
      setResume(res.ok ? { texte: body.resume, modele: body.modele } : { erreur: body.detail ?? "Résumé indisponible" });
    } catch {
      setResume({ erreur: "API locale injoignable" });
    }
  };
  return (
    <article className="avis">
      <div className="rang">
        {String(rang).padStart(2, "0")}
        <small>score {decimal(r.score)}</small>
      </div>
      <div style={{ minWidth: 0 }}>
        <h3><a href={r.url} target="_blank" rel="noreferrer">{r.objet}</a></h3>
        <div className="ligne">
          <span>{r.acheteur}</span>
          <span className="mono">Dép. {r.departements.slice(0, 4).join(", ") || "n. c."}{r.departements.length > 4 ? "…" : ""}</span>
          <span>Limite : {dateFr(r.date_limite)} <span className="mono">({j} j)</span></span>
          <span className={`tag ${VERDICT[r.verdict] ?? ""}`}>{r.verdict}</span>
        </div>
        <ScoreBar composantes={r.composantes} delay={delay} />
        <button className="btn ghost" style={{ padding: "4px 10px", fontSize: "0.82rem" }} aria-expanded={open} onClick={() => setOpen(!open)}>
          {open ? "Masquer l'analyse" : "Voir l'analyse"}
        </button>
        {open && (
          <div className="cols cols-2" style={{ marginTop: 12, gap: 22 }}>
            <div>
              <h4 className="kicker" style={{ margin: "0 0 6px" }}>Grille go / no-go</h4>
              <div className="gng">
                {r.go_no_go.map((g) => (
                  <div key={g.critere}>
                    <span className={`mark ${g.statut}`} aria-hidden="true">{SYMB[g.statut]}</span>
                    <span><b>{g.critere}</b> <span className="sr-only">({g.statut})</span>— {g.detail}</span>
                  </div>
                ))}
              </div>
              <h4 className="kicker" style={{ margin: "16px 0 6px" }}>Historique DECP de l'acheteur</h4>
              {h.niveau ? (
                <dl className="meta">
                  <dt>Rapprochement</dt><dd>{h.rapprochement === "siret" ? "par SIRET" : h.rapprochement === "nom" ? "par nom" : "aucun (repli départemental)"}</dd>
                  <dt>Groupe CPV</dt><dd className="mono">{h.groupe_cpv}</dd>
                  {h.nb_marches != null && <><dt>Marchés passés</dt><dd>{entier(Number(h.nb_marches))} depuis 2021</dd></>}
                  <dt>Offres moyennes</dt><dd>{h.offres_moyennes == null ? "non renseigné" : decimal(Number(h.offres_moyennes))}{h.niveau_concurrence === "departement" ? " (département)" : ""}</dd>
                  <dt>Offre unique</dt><dd>{h.taux_offre_unique == null ? "non renseigné" : pct(Number(h.taux_offre_unique))}</dd>
                  {h.titulaire_principal_part != null && (
                    <><dt>Titulaire principal</dt><dd>{h.titulaire_principal ?? "nom non affiché"} — {pct(Number(h.titulaire_principal_part), 0)} des marchés</dd></>
                  )}
                </dl>
              ) : <p className="small muted">Aucun historique rapproché pour cet acheteur et ce type d'achat.</p>}
            </div>
            <div>
              <h4 className="kicker" style={{ margin: "0 0 6px" }}>Décomposition du score</h4>
              <table>
                <thead><tr><th>Composante</th><th className="r">Valeur</th><th className="r">Poids</th><th className="r">Points</th></tr></thead>
                <tbody>
                  {Object.entries(r.composantes).map(([k, c]) => (
                    <tr key={k}><td>{LIBELLES[k]}</td><td className="r">{c.valeur.toFixed(2)}</td><td className="r">{c.poids}</td><td className="r">{decimal(c.contribution)}</td></tr>
                  ))}
                  <tr><td><b>Score</b></td><td /><td /><td className="r"><b>{decimal(r.score)}</b></td></tr>
                </tbody>
              </table>
              <dl className="meta" style={{ marginTop: 12 }}>
                <dt>Procédure</dt><dd>{r.procedure ?? "n. c."}</dd>
                <dt>Montant estimé</dt><dd>{r.montant_estime ? euros(r.montant_estime) : "non publié"}</dd>
                <dt>Lots</dt><dd>{r.nb_lots}</dd>
                <dt>CPV</dt><dd>{r.cpv.map((c) => <div key={c.code}><span className="mono">{c.code}</span> {c.libelle}</div>)}</dd>
                <dt>Avis</dt><dd><a href={r.url} target="_blank" rel="noreferrer">BOAMP {r.idweb}</a></dd>
              </dl>
              {r.extrait && <p className="small muted" style={{ marginTop: 10 }}>« {r.extrait.slice(0, 300)}{r.extrait.length > 300 ? "…" : ""} »</p>}
              {api && (
                <div style={{ marginTop: 10 }}>
                  <button className="btn ghost" onClick={demanderResume} disabled={resume !== null && !resume.texte && !resume.erreur}>Résumer l'avis (LLM)</button>
                  {resume?.texte && <div className="notice" style={{ marginTop: 8 }}><b>Résumé généré par {resume.modele}</b> — à vérifier sur l'avis officiel.<br />{resume.texte}</div>}
                  {resume?.erreur && <p className="small muted">{resume.erreur}</p>}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </article>
  );
}
