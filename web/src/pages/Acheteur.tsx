import { Link, useParams } from "react-router-dom";
import Chart from "../components/Chart";
import { hbar, vbar } from "../components/charts";
import DataTable from "../components/DataTable";
import { CountUp, Reveal } from "../components/Motion";
import { fetchJson } from "../lib/data";
import { dateFr, decimal, entier, euros, pct } from "../lib/format";
import { useAsync } from "../lib/hooks";
import type { AcheteurLigne } from "./Acheteurs";

interface Fiche extends AcheteurLigne {
  par_cpv: { groupe_code: string; groupe_libelle: string; nb_marches: number; montant_median: number | null; offres_moyennes: number | null; taux_offre_unique: number | null; part_pme: number | null }[];
  par_annee: { annee: number; nb_marches: number; montant: number | null }[];
  titulaires: { titulaire: string; nom_publiable: boolean; categorie: string; nb_marches: number; montant: number | null }[];
  marches_recents: { date_notification: string; objet: string | null; montant_marche: number | null; offres_recues: number | null; code_cpv: string; procedure_code: string }[];
}

export default function Acheteur() {
  const { id } = useParams();
  const { data: f, error } = useAsync<Fiche>(() => fetchJson(`acheteurs/${id}.json`), [id]);
  if (error) return (
    <div className="container rubrique"><h1>Fiche indisponible</h1>
      <p>Les fiches statiques couvrent les 1 000 acheteurs les plus actifs. <Link to="/acheteurs">Revenir à la liste</Link>.</p></div>
  );
  if (!f) return <div className="container rubrique"><p className="muted">Chargement…</p></div>;
  const figures: [string, number | null, (x: number) => string, boolean?][] = [
    ["Marchés depuis 2021", f.nb_marches, entier],
    ["Montant attribué", f.montant_total, euros],
    ["Offres reçues en moyenne", f.offres_moyennes, (x) => decimal(x)],
    ["Marchés à offre unique", f.taux_offre_unique, (x) => pct(x), true],
    ["Part des PME (en nombre)", f.part_pme, (x) => pct(x)],
  ];
  return (
    <div className="container">
      <section className="rubrique" style={{ marginTop: 28 }}>
        <header>
          <div>
            <div className="kicker"><Link to="/acheteurs">Fiches acheteur</Link> · SIRET <span className="mono">{f.acheteur_id}</span></div>
            <h1>{f.acheteur_nom}</h1>
          </div>
          <p>{f.acheteur_categorie} · {f.nom_departement} ({f.departement_code}) · {f.nom_region}</p>
        </header>
        <div className="figures">
          {figures.map(([l, v, fmt, alert]) => (
            <div className={`figure${alert ? " alert" : ""}`} key={l}>
              <div className="v"><CountUp value={v} format={fmt} /></div>
              <div className="l">{l}</div>
              {v == null && <div className="s">non renseigné dans les DECP</div>}
            </div>
          ))}
        </div>
      </section>
      <section className="rubrique">
        <div className="cols cols-2 col-rule">
          <Reveal className="panel">
            <h3>Ce qu'il achète (groupes CPV)</h3>
            <Chart className="chart tall" label="Marchés par groupe CPV" deps={[f]}
              build={(t) => hbar(t, f.par_cpv.slice(0, 10).map((c) => ({ label: c.groupe_libelle ?? c.groupe_code, value: c.nb_marches })), entier)} />
          </Reveal>
          <Reveal className="panel" delay={0.08}>
            <h3>Marchés par année</h3>
            <Chart label="Marchés par année" deps={[f]} build={(t) => vbar(t, f.par_annee.map((a) => ({ label: String(a.annee), value: a.nb_marches })), entier)} />
            <DataTable caption="Marchés par année" headers={["Année", "Marchés", "Montant"]} rows={f.par_annee.map((a) => [a.annee, entier(a.nb_marches), euros(a.montant)])} />
          </Reveal>
        </div>
      </section>
      <section className="rubrique">
        <header><div><div className="kicker">Concurrence par type d'achat</div><h2>Montants typiques et intensité concurrentielle</h2></div></header>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Groupe CPV</th><th className="r">Marchés</th><th className="r">Montant médian</th><th className="r">Offres moy.</th><th className="r">Offre unique</th><th className="r">Part PME</th></tr></thead>
            <tbody>
              {f.par_cpv.map((c) => (
                <tr key={c.groupe_code}>
                  <td><span className="mono muted">{c.groupe_code}</span> {c.groupe_libelle}</td>
                  <td className="r">{entier(c.nb_marches)}</td><td className="r">{euros(c.montant_median)}</td>
                  <td className="r">{decimal(c.offres_moyennes)}</td><td className="r">{pct(c.taux_offre_unique)}</td><td className="r">{pct(c.part_pme)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="rubrique">
        <div className="cols cols-2 col-rule">
          <div className="panel">
            <h3>Principaux titulaires</h3>
            <table>
              <thead><tr><th>Titulaire</th><th>Catégorie</th><th className="r">Marchés</th><th className="r">Montant</th></tr></thead>
              <tbody>
                {f.titulaires.map((t, i) => (
                  <tr key={i}><td className={t.nom_publiable ? "" : "muted"}>{t.titulaire}</td><td className="mono small">{t.categorie}</td><td className="r">{entier(t.nb_marches)}</td><td className="r">{euros(t.montant)}</td></tr>
                ))}
              </tbody>
            </table>
            <p className="source">Noms affichés uniquement pour les personnes morales avérées (RGPD : un entrepreneur individuel est une personne physique).</p>
          </div>
          <div className="panel">
            <h3>Derniers marchés notifiés</h3>
            <ul className="list-plain small">
              {f.marches_recents.map((m, i) => (
                <li key={i}>
                  <div>{m.objet ?? "Objet non renseigné"}</div>
                  <div className="muted mono" style={{ fontSize: "0.74rem" }}>{dateFr(m.date_notification)} · CPV {m.code_cpv} · {euros(m.montant_marche)} · {m.offres_recues ?? "?"} offre(s)</div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
