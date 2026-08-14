// Page d'ouverture racontée comme une étude de cas :
// constat chiffré -> problème -> démarche -> produit en action -> résultats -> accès.
import { useMemo } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import AvisCard from "../components/AvisCard";
import FranceMap from "../components/FranceMap";
import { CountUp, EASE, Reveal } from "../components/Motion";
import { ScoreLegend } from "../components/ScoreBar";
import { REPO } from "../components/Layout";
import { aggregate, metric } from "../lib/cube";
import { fetchJson } from "../lib/data";
import { dateFr, decimal, entier, euros, pct } from "../lib/format";
import { MEASURES, useAsync, useBase, useCube, useRegionOf } from "../lib/hooks";
import type { RadarRun } from "../lib/radar";
import { useReducedMotion } from "../lib/theme";

interface Ev { resultats: { jeu: string; methode: string; "ndcg@10": number; "p@10": number }[]; corpus: { test: number } }

const RECENT = [2024, 2025, 2026];

export default function Accueil() {
  const { data: base } = useBase();
  const { data: rows } = useCube();
  const regionOf = useRegionOf(base?.dims);
  const ev = useAsync<Ev>(() => fetchJson("evaluation.json")).data;
  const demo = useAsync<RadarRun>(() => fetchJson("radar/ardoise-batiment.json")).data;
  const reduced = useReducedMotion();

  const s = useMemo(() => {
    if (!rows || !base) return null;
    const cat = base.catalog;
    const all = aggregate(rows, MEASURES).get("*")!;
    const recent = aggregate(rows, MEASURES, { annee: RECENT }).get("*")!;
    const deps = aggregate(rows, MEASURES, { annee: RECENT }, (r) => String(r.departement));
    const values: Record<string, number | null> = {};
    for (const code of Object.keys(base.carte.departements)) {
      const d = deps.get(code);
      values[code] = d && d.nb_marches_offres >= 30 ? metric(cat, "taux_offre_unique", d) : null;
    }
    return {
      marches: metric(cat, "nombre_marches", all), montant: metric(cat, "montant_total", all),
      unique: metric(cat, "taux_offre_unique", recent), renseignes: recent.nb_marches_offres,
      pmeN: metric(cat, "part_pme_nombre", all), pmeM: metric(cat, "part_pme_montant", all),
      offres: metric(cat, "offres_moyennes", recent), values,
    };
  }, [rows, base]);

  const hyb = (jeu: string) => ev?.resultats.find((r) => r.jeu.startsWith(jeu) && r.methode.startsWith("Hybride ("));
  const bm25 = (jeu: string) => ev?.resultats.find((r) => r.jeu.startsWith(jeu) && r.methode === "BM25");

  return (
    <div className="container">
      {/* 1. Constat */}
      <section style={{ paddingTop: 34 }}>
        <div className="cols cols-main" style={{ alignItems: "start" }}>
          <div>
            <motion.div className="kicker" initial={reduced ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4, ease: EASE }}>
              Étude de cas · commande publique française · 2021 → 2026
            </motion.div>
            <motion.h1 initial={reduced ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE, delay: 0.05 }}>
              Depuis 2024, {s ? <span style={{ color: "var(--single)" }}>{pct(s.unique, 0)}</span> : "…"} des marchés publics n'ont reçu qu'une seule offre.
            </motion.h1>
            <motion.p className="lead" initial={reduced ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE, delay: 0.15 }}>
              Des appels d'offres sans concurrence d'un côté ; de l'autre, des PME qui renoncent faute de temps pour la veille.
              Radar Marchés Publics relie les deux : il trouve, qualifie et priorise les avis ouverts à partir de
              l'historique réel des attributions.
            </motion.p>
            <div className="figures" style={{ marginTop: 22 }}>
              <div className="figure alert">
                <div className="v"><CountUp value={s?.unique ?? null} format={(x) => pct(x)} /></div>
                <div className="l">marchés à offre unique (2024 → 2026)</div>
                <div className="s">sur {s ? entier(s.renseignes) : "…"} marchés renseignés</div>
              </div>
              <div className="figure">
                <div className="v"><CountUp value={s?.marches ?? null} format={entier} /></div>
                <div className="l">marchés analysés depuis 2021</div>
                <div className="s">DECP nettoyées, dédoublonnées</div>
              </div>
              <div className="figure">
                <div className="v"><CountUp value={s?.offres ?? null} format={(x) => decimal(x)} /></div>
                <div className="l">offres reçues en moyenne</div>
                <div className="s">2024 → 2026</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 22 }}>
              <Link className="btn beacon" to="/radar">Ouvrir le radar</Link>
              <Link className="btn ghost" to="/panorama">Explorer le panorama</Link>
            </div>
          </div>
          <div>
            {base && s && (
              <FranceMap carte={base.carte} values={s.values} regionOf={regionOf} format={(x) => pct(x)}
                label="Carte : taux de marchés à offre unique par département de l'acheteur, 2024 à 2026" />
            )}
            <p className="source">Taux d'offre unique par département de l'acheteur, 2024 → 2026. Plus foncé = moins de concurrence. Source : DECP (decp.info), version du {base ? dateFr(base.meta.decp.version) : "…"}.</p>
          </div>
        </div>
      </section>

      {/* 2. Problème */}
      <section className="rubrique">
        <header>
          <div><div className="kicker">01 · Le problème</div><h2>Les PME gagnent beaucoup de marchés, mais de petits marchés</h2></div>
        </header>
        <div className="cols cols-2 col-rule">
          <Reveal>
            <div className="figures" style={{ borderTop: 0 }}>
              <div className="figure"><div className="v">{s ? pct(s.pmeN, 0) : "…"}</div><div className="l">des marchés vont à des PME</div></div>
              <div className="figure"><div className="v">{s ? pct(s.pmeM, 0) : "…"}</div><div className="l">du montant attribué</div></div>
            </div>
            <p className="small muted" style={{ marginTop: 10 }}>Titulaires de catégorie connue, 2021 → 2026, {s ? euros(s.montant) : "…"} de montants déclarés.</p>
          </Reveal>
          <Reveal delay={0.08}>
            <p>
              Un dirigeant de PME consacre plusieurs heures par semaine à éplucher le BOAMP et les plateformes d'achat,
              sans savoir si l'acheteur reçoit d'habitude deux offres ou quinze, ni si un titulaire sortant est installé.
              Résultat : des réponses dispersées, des occasions manquées, et une concurrence faible sur une partie des marchés.
            </p>
            <p className="small muted">Hypothèse de cadrage, à valider en entretiens : voir la note de cadrage et le business case.</p>
          </Reveal>
        </div>
      </section>

      {/* 3. Démarche */}
      <section className="rubrique">
        <header>
          <div><div className="kicker">02 · La démarche</div><h2>Du cadrage à la recette, comme une mission de conseil</h2></div>
        </header>
        <ol className="steps cols cols-2" style={{ gap: "0 28px" }}>
          {[
            ["Cadrer", "Note de cadrage, personas (dirigeant de PME, chargé d'affaires), parcours de veille."],
            ["Modéliser", "Processus de veille et de réponse AS-IS / TO-BE en BPMN ; user stories INVEST et MVP MoSCoW."],
            ["Construire la donnée", "Entrepôt DuckDB + dbt en étoile, tests dbt automatisés, rapport de qualité chiffré, couche sémantique."],
            ["Construire l'IA", "Score hybride expliqué (embeddings, BM25, CPV, territoire, historique de concurrence)."],
            ["Mesurer", "Évaluation reproductible sur des avis réels jamais vus au réglage ; analyse d'erreurs."],
            ["Sécuriser", "RGPD (titulaires personnes physiques masqués), AI Act, plan de recette, journal des décisions."],
          ].map(([t, d]) => (
            <li key={t}><span><b>{t}.</b> {d}</span></li>
          ))}
        </ol>
        <p style={{ marginTop: 12 }}><a href={`${REPO}/tree/main/docs`}>Lire les livrables Business Analyst</a></p>
      </section>

      {/* 4. Produit en action */}
      {demo && (
        <section className="rubrique">
          <header>
            <div><div className="kicker">03 · Le produit en action</div><h2>Ardoise Bâtiment : trois avis à regarder en priorité</h2></div>
            <p>
              <span className="tag fictif">Profil fictif</span> PME du BTP de 80 salariés, gros œuvre et rénovation énergétique,
              Île-de-France. Classement calculé sur {base ? entier(base.meta.boamp.avis_ouverts_retenus) : "…"} avis ouverts au {dateFr(demo.snapshot_date)}.
            </p>
          </header>
          <ScoreLegend />
          {demo.resultats.slice(0, 3).map((r, i) => (
            <Reveal key={r.idweb} delay={i * 0.08}>
              <AvisCard r={r} rang={i + 1} snapshot={demo.snapshot_date} delay={0.2 + i * 0.08} />
            </Reveal>
          ))}
          <Link className="btn" to="/radar" style={{ marginTop: 10 }}>Voir les 30 avis et les deux autres profils</Link>
        </section>
      )}

      {/* 5. Résultats */}
      <section className="rubrique">
        <header>
          <div><div className="kicker">04 · Les résultats</div><h2>Ce que mesure l'évaluation, sans enjoliver</h2></div>
          <p>Sur {ev ? entier(ev.corpus.test) : "…"} avis de test jamais utilisés pour le réglage, la vérité terrain étant leurs codes CPV.</p>
        </header>
        <div className="figures">
          <div className="figure"><div className="v">{hyb("Q1") ? decimal(hyb("Q1")!["ndcg@10"], 2) : "…"}</div><div className="l">nDCG@10 de l'hybride, requêtes « profil CPV »</div><div className="s">BM25 seul : {bm25("Q1") ? decimal(bm25("Q1")!["ndcg@10"], 2) : "…"}</div></div>
          <div className="figure"><div className="v">{hyb("Q2") ? decimal(hyb("Q2")!["ndcg@10"], 2) : "…"}</div><div className="l">nDCG@10 de l'hybride, requêtes « avis exemple »</div><div className="s">BM25 seul : {bm25("Q2") ? decimal(bm25("Q2")!["ndcg@10"], 2) : "…"}</div></div>
          <div className="figure"><div className="v">{hyb("Q2") ? pct(hyb("Q2")!["p@10"], 0) : "…"}</div><div className="l">des 10 premiers résultats dans le bon groupe CPV</div><div className="s">borne basse : codes CPV bruités</div></div>
        </div>
        <p className="small" style={{ marginTop: 12 }}>
          Le texte seul est difficile : l'hybride devance BM25 de peu. C'est pourquoi le score final ajoute le CPV, le territoire,
          la taille et la concurrence historique, et montre toujours sa décomposition. <Link to="/methode">Méthode complète</Link>.
        </p>
      </section>

      {/* 6. Accès */}
      <section className="rubrique">
        <div className="cols cols-2 col-rule">
          <div>
            <h2>Essayer</h2>
            <p>La démo en ligne contient le panorama, 1 000 fiches acheteur et le radar précalculé pour trois profils fictifs. L'application locale classe les avis pour votre propre profil et rafraîchit le BOAMP en direct.</p>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <Link className="btn beacon" to="/radar">Ouvrir le radar</Link>
              <a className="btn ghost" href={REPO}>Code source et installation</a>
            </div>
          </div>
          <div>
            <h2>Données</h2>
            <ul className="list-plain small">
              <li>DECP consolidées (decp.info, data.gouv.fr) · version du {base ? dateFr(base.meta.decp.version) : "…"}</li>
              <li>BOAMP (DILA) · instantané du {base ? dateFr(base.meta.boamp.snapshot_date) : "…"}</li>
              <li>SIRENE (API Recherche d'entreprises) · CPV 2008 · COG INSEE · IGN Admin Express</li>
              <li>Licence Ouverte 2.0 · CC BY 4.0 pour la nomenclature CPV</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
