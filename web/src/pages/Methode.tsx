import { fetchJson, type Catalog } from "../lib/data";
import { decimal, entier, pct, dateFr } from "../lib/format";
import { useAsync, useBase } from "../lib/hooks";
import { REPO } from "../components/Layout";

interface Qualite {
  lignes_source: number;
  entonnoir: { etape: string; lignes: number; total?: boolean }[];
  marches: { identifiants_source: number; marches_apres_r2c: number; fusionnes_r2c: number };
  completude: Record<string, number>;
  sirene: { titulaires_enrichis: number; titulaires: number; part_montant_couverte: number; entrepreneurs_individuels_detectes: number };
}
interface Evaluation {
  snapshot_date: string; alpha: number;
  corpus: { avis_avec_cpv: number; reglage: number; test: number };
  resultats: { jeu: string; methode: string; requetes: number; "p@10": number; "ndcg@10": number; "r@50": number; "ndcg@10_ic95": number[] }[];
}

const DOCS: [string, string][] = [
  ["Note de cadrage", "docs/ba/01-note-de-cadrage.md"],
  ["Personas et parcours", "docs/ba/02-personas-parcours.md"],
  ["Processus AS-IS / TO-BE (BPMN)", "docs/ba/03-processus-bpmn.md"],
  ["User stories et MVP", "docs/ba/04-user-stories.md"],
  ["Arbre de KPI et business case", "docs/ba/05-kpi-business-case.md"],
  ["Risques, RGPD et AI Act", "docs/ba/06-risques-conformite.md"],
  ["Plan de recette", "docs/ba/07-plan-de-recette.md"],
  ["Journal des décisions", "docs/decisions.md"],
  ["Rapport de qualité des données", "docs/qualite-donnees.md"],
  ["Évaluation du radar", "docs/evaluation-radar.md"],
];

export default function Methode() {
  const { data: base } = useBase();
  const q = useAsync<Qualite>(() => fetchJson("qualite.json")).data;
  const ev = useAsync<Evaluation>(() => fetchJson("evaluation.json")).data;
  const cat: Catalog | undefined = base?.catalog;
  return (
    <div className="container">
      <section className="rubrique" style={{ marginTop: 28 }}>
        <header>
          <div><div className="kicker">Méthode</div><h1>D'où viennent les chiffres</h1></div>
          <p>Toutes les données sont publiques. Chaque chiffre du site est recalculable par une commande documentée dans le dépôt.</p>
        </header>
        <div className="cols cols-3 col-rule">
          <div className="panel">
            <h3>DECP</h3>
            <p className="small">Données essentielles de la commande publique : les marchés attribués (acheteur, titulaire, montant, offres reçues). Version consolidée par decp.info, publiée sur data.gouv.fr, du {base ? dateFr(base.meta.decp.version) : "…"}.</p>
            <p className="source">Licence Ouverte 2.0 (Etalab)</p>
          </div>
          <div className="panel">
            <h3>BOAMP</h3>
            <p className="small">Bulletin officiel des annonces des marchés publics : les avis en cours. Instantané pris le {base ? dateFr(base.meta.boamp.snapshot_date) : "…"} via l'API de la DILA ({base ? entier(base.meta.boamp.avis_ouverts_retenus) : "…"} avis ouverts retenus).</p>
            <p className="source">Licence Ouverte 2.0 (DILA)</p>
          </div>
          <div className="panel">
            <h3>SIRENE, CPV, géographie</h3>
            <p className="small">API Recherche d'entreprises pour la catégorie des titulaires ; nomenclature CPV 2008 (libellés français) ; départements et régions (COG INSEE) ; contours IGN Admin Express simplifiés.</p>
            <p className="source">Licence Ouverte 2.0 · CC BY 4.0 (CPV)</p>
          </div>
        </div>
      </section>

      {q && (
        <section className="rubrique">
          <header>
            <div><div className="kicker">Qualité des données</div><h2>Entonnoir de nettoyage</h2></div>
            <p>Les DECP agrègent de nombreuses sources : un même marché peut être publié plusieurs fois. Chaque règle est appliquée dans l'entrepôt dbt et son impact est mesuré.</p>
          </header>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Étape</th><th className="r">Lignes (marché × titulaire)</th></tr></thead>
              <tbody>
                {q.entonnoir.map((e) => (
                  <tr key={e.etape}><td>{e.total ? <b>{e.etape}</b> : e.etape}</td><td className="r">{e.total ? <b>{entier(e.lignes)}</b> : entier(e.lignes)}</td></tr>
                ))}
                <tr><td>R2c – accords-cadres multi-attributaires regroupés</td><td className="r">{entier(q.marches.identifiants_source)} → {entier(q.marches.marches_apres_r2c)} marchés</td></tr>
              </tbody>
            </table>
          </div>
          <p className="small" style={{ marginTop: 10 }}>
            Nombre d'offres exploitable : {pct(q.completude.offres_exploitables)} des lignes ; catégorie du titulaire connue : {pct(q.completude.categorie_titulaire)} ;
            titulaires enrichis via SIRENE : {entier(q.sirene.titulaires_enrichis)}, soit {pct(q.sirene.part_montant_couverte)} du montant. <a href={`${REPO}/blob/main/docs/qualite-donnees.md`}>Rapport complet</a>.
          </p>
        </section>
      )}

      {ev && (
        <section className="rubrique">
          <header>
            <div><div className="kicker">Évaluation du radar</div><h2>Le moteur de recherche, mesuré sur des avis réels</h2></div>
            <p>
              Vérité terrain : les codes CPV des avis. {entier(ev.corpus.test)} avis de test, jamais utilisés pour le réglage
              (alpha = {ev.alpha} choisi sur {entier(ev.corpus.reglage)} autres avis). Q1 : requêtes construites depuis les
              libellés CPV ; Q2 : un avis sert d'exemple pour retrouver les avis du même groupe.
            </p>
          </header>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Jeu</th><th>Méthode</th><th className="r">Requêtes</th><th className="r">Précision@10</th><th className="r">nDCG@10 [IC 95 %]</th><th className="r">Rappel@50</th></tr></thead>
              <tbody>
                {ev.resultats.map((r) => (
                  <tr key={r.jeu + r.methode}>
                    <td className="small">{r.jeu}</td>
                    <td>{r.methode.startsWith("Hybride (") ? <b>{r.methode}</b> : r.methode}</td>
                    <td className="r">{r.requetes}</td><td className="r">{decimal(r["p@10"], 3)}</td>
                    <td className="r">{decimal(r["ndcg@10"], 3)} [{decimal(r["ndcg@10_ic95"][0], 3)} ; {decimal(r["ndcg@10_ic95"][1], 3)}]</td>
                    <td className="r">{decimal(r["r@50"], 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small" style={{ marginTop: 10 }}>
            Lecture : l'hybride devance BM25 de peu (intervalles de confiance qui se recouvrent) et nettement les embeddings seuls.
            Les scores sont une borne basse : une partie des « erreurs » sont des avis utiles codés dans une classe CPV voisine.
            <a href={`${REPO}/blob/main/docs/evaluation-radar.md`}> Protocole et analyse d'erreurs</a>.
          </p>
        </section>
      )}

      {cat && (
        <section className="rubrique">
          <header><div><div className="kicker">Glossaire</div><h2>Définitions des indicateurs</h2></div>
            <p>Source unique : <span className="mono">semantic/metrics.yml</span>. Le site recalcule les ratios à partir des mêmes mesures additives.</p></header>
          <dl className="meta" style={{ gap: "10px 22px" }}>
            {Object.entries(cat.metrics).map(([k, m]) => (
              <div key={k} style={{ display: "contents" }}>
                <dt>{m.label}</dt>
                <dd className="small">{m.definition}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      <section className="rubrique">
        <header><div><div className="kicker">Démarche Business Analyst</div><h2>Les livrables</h2></div></header>
        <ul className="list-plain cols cols-2" style={{ gap: "0 28px" }}>
          {DOCS.map(([l, p]) => <li key={p}><a href={`${REPO}/blob/main/${p}`}>{l}</a></li>)}
          <li><a href={`${import.meta.env.BASE_URL}dbt-docs/`}>Documentation dbt : modèles, tests et lignage interactif</a></li>
        </ul>
      </section>

      <section className="rubrique">
        <header><div><div className="kicker">Limites</div><h2>Ce que le radar ne fait pas</h2></div></header>
        <ul className="steps">
          <li><span>Les montants des DECP sont déclaratifs ; pour un accord-cadre, c'est un plafond, pas une dépense.</span></li>
          <li><span>Le nombre d'offres n'est renseigné massivement que depuis 2024 : les tendances de concurrence antérieures sont fragiles.</span></li>
          <li><span>La démo statique repose sur un instantané BOAMP daté ; l'application locale peut le rafraîchir.</span></li>
          <li><span>Le résumé par LLM est optionnel : sans clé fournie par l'utilisateur, aucune sortie LLM n'est affichée ni simulée.</span></li>
          <li><span>Le score aide à trier ; la décision de répondre reste humaine, avis officiel à l'appui.</span></li>
        </ul>
      </section>
    </div>
  );
}
