import { useEffect, useMemo, useRef, useState } from "react";
import Chart from "../components/Chart";
import { hbar, line, vbar } from "../components/charts";
import DataTable from "../components/DataTable";
import FranceMap from "../components/FranceMap";
import { CountUp, Reveal } from "../components/Motion";
import { aggregate, metric, type Filters } from "../lib/cube";
import { fetchJson } from "../lib/data";
import { format } from "../lib/format";
import { MEASURES, useAsync, useBase, useCube, useRegionOf } from "../lib/hooks";
import { useReducedMotion } from "../lib/theme";

const ANNEES = [2021, 2022, 2023, 2024, 2025, 2026];
const KPIS = ["nombre_marches", "montant_total", "part_pme_nombre", "part_pme_montant", "offres_moyennes", "taux_offre_unique"];
const MAP_METRICS = ["nombre_marches", "taux_offre_unique", "part_pme_nombre", "offres_moyennes"];
const MIN_OFFRES = 30; // nombre minimal de marchés avec offres renseignées pour publier un ratio de concurrence

interface NonAdd {
  national: Record<string, number>;
  annee: Record<string, number>[];
  periode_concurrence: string;
}

export default function Panorama() {
  const { data: base } = useBase();
  const { data: rows, error } = useCube();
  const na = useAsync<NonAdd>(() => fetchJson("non_additifs.json")).data;
  const regionOf = useRegionOf(base?.dims);
  const [f, setF] = useState<Filters>({});
  const [mapMetric, setMapMetric] = useState("taux_offre_unique");
  const [mapYear, setMapYear] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const reduced = useReducedMotion();
  const timer = useRef<number | null>(null);

  const set = (dim: string, v: string) => setF((p) => ({ ...p, [dim]: v ? [dim === "annee" ? Number(v) : v] : [] }));
  const cat = base?.catalog;
  const fmt = (m: string) => (x: number) => format(x, cat?.metrics[m]?.format ?? "entier");

  const total = useMemo(() => (rows ? aggregate(rows, MEASURES, f, undefined, regionOf).get("*") : undefined), [rows, f, regionOf]);
  const byYear = useMemo(() => {
    if (!rows) return new Map();
    const { annee: _a, ...rest } = f;
    void _a;
    return aggregate(rows, MEASURES, rest, (r) => String(r.annee), regionOf);
  }, [rows, f, regionOf]);
  const byDep = useMemo(() => {
    if (!rows) return new Map();
    const ff: Filters = { ...f, departement: [] };
    if (mapYear) ff.annee = [mapYear];
    return aggregate(rows, MEASURES, ff, (r) => String(r.departement), regionOf);
  }, [rows, f, mapYear, regionOf]);
  const groupBy = (dim: string, extra: Filters = {}) =>
    rows ? aggregate(rows, MEASURES, { ...f, ...extra }, (r) => String(r[dim]), regionOf) : new Map();
  const byDiv = useMemo(() => groupBy("division_cpv"), [rows, f]); // eslint-disable-line react-hooks/exhaustive-deps
  const byDiv24 = useMemo(() => groupBy("division_cpv", { annee: f.annee?.length ? f.annee.filter((a) => Number(a) >= 2024) : [2024, 2025, 2026] }), [rows, f]); // eslint-disable-line react-hooks/exhaustive-deps
  const byProc = useMemo(() => groupBy("procedure"), [rows, f]); // eslint-disable-line react-hooks/exhaustive-deps
  const byAch = useMemo(() => groupBy("categorie_acheteur"), [rows, f]); // eslint-disable-line react-hooks/exhaustive-deps

  // Curseur temporel : fait défiler les années une fois (pas de boucle).
  useEffect(() => {
    if (!playing) return;
    let i = 0;
    setMapYear(ANNEES[0]);
    timer.current = window.setInterval(() => {
      i += 1;
      if (i >= ANNEES.length) {
        setPlaying(false);
        return;
      }
      setMapYear(ANNEES[i]);
    }, reduced ? 200 : 900);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [playing, reduced]);

  if (error) return <div className="container rubrique"><p>Données indisponibles : {error}</p></div>;
  if (!base || !cat) return <div className="container rubrique"><p className="muted">Chargement…</p></div>;

  const divLabel = new Map(base.dims.divisions_cpv.map((d) => [d.code, d.libelle]));
  const procLabel = new Map(base.dims.procedures.map((p) => [p.procedure_code, p.procedure_libelle]));
  const depValues: Record<string, number | null> = {};
  for (const code of Object.keys(base.carte.departements)) {
    const s = byDep.get(code);
    const isConc = mapMetric === "taux_offre_unique" || mapMetric === "offres_moyennes";
    depValues[code] = !s || (isConc && s.nb_marches_offres < MIN_OFFRES) ? null : metric(cat, mapMetric, s);
  }
  const years = ANNEES.map((y) => ({ label: String(y), s: byYear.get(String(y)) }));
  const rank = (m: Map<string, Record<string, number>>, name: string, labels: Map<string, string>, n = 12, minOffres = 0) =>
    [...m.entries()]
      .filter(([, s]) => s.nb_marches_offres >= minOffres && s.nb_marches > 0)
      .map(([k, s]) => ({ label: labels.get(k) ?? k, value: metric(cat, name, s) }))
      .filter((d) => d.value != null)
      .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))
      .slice(0, n);
  const divTop = rank(byDiv, "nombre_marches", divLabel);
  const divUnique = rank(byDiv24, "taux_offre_unique", divLabel, 12, 200);
  const divPme = rank(byDiv, "part_pme_nombre", divLabel, 12).filter((d) => d.label !== "Non classé");
  const proc = rank(byProc, "nombre_marches", procLabel, 8);
  const ach = rank(byAch, "nombre_marches", new Map(), 10);
  const pickers: [string, string, { v: string; l: string }[]][] = [
    ["annee", "Année", ANNEES.map((a) => ({ v: String(a), l: String(a) }))],
    ["region", "Région", base.dims.regions.filter((r) => r.code_region !== "NR").map((r) => ({ v: r.code_region, l: r.nom_region }))],
    ["division_cpv", "Secteur (division CPV)", base.dims.divisions_cpv.map((d) => ({ v: d.code, l: `${d.code} · ${d.libelle}` }))],
    ["type_marche", "Type de marché", ["Travaux", "Services", "Fournitures"].map((x) => ({ v: x, l: x }))],
    ["procedure", "Procédure", base.dims.procedures.map((p) => ({ v: p.procedure_code, l: p.procedure_libelle }))],
    ["categorie_acheteur", "Type d'acheteur", ["Commune", "Groupement de communes", "Département", "Région", "État", "Établissement hospitalier", "EPIC", "Syndicat mixte", "Département outre-mer", "Non renseignée"].map((x) => ({ v: x, l: x }))],
  ];

  return (
    <div className="container">
      <section className="rubrique" style={{ marginTop: 28 }}>
        <header>
          <div>
            <div className="kicker">Panorama · DECP 2021 → {base.meta.decp.date_max_notification.slice(0, 4)}</div>
            <h1>La commande publique, en chiffres vérifiables</h1>
          </div>
          <p>
            Marchés attribués depuis 2021, nettoyés et dédoublonnés dans l'entrepôt. Chaque chiffre vient de la couche
            sémantique : survolez un libellé dans la page <a href="#/methode">Méthode</a> pour sa définition.
          </p>
        </header>
        <div className="filters sticky" role="group" aria-label="Filtres du panorama">
          {pickers.map(([dim, label, opts]) => (
            <div className="field" key={dim}>
              <label htmlFor={`f-${dim}`}>{label}</label>
              <select id={`f-${dim}`} value={String(f[dim]?.[0] ?? "")} onChange={(e) => set(dim, e.target.value)}>
                <option value="">Tous</option>
                {opts.map((o) => <option key={o.v} value={o.v}>{o.l}</option>)}
              </select>
            </div>
          ))}
          <button className="btn ghost" onClick={() => setF({})} disabled={!Object.values(f).some((v) => v?.length)}>Réinitialiser</button>
        </div>
        {!rows ? <p className="muted">Chargement du cube de données…</p> : (
          <div className="figures" style={{ marginTop: 18 }}>
            {KPIS.map((k) => (
              <div className={`figure${k === "taux_offre_unique" ? " alert" : ""}`} key={k}>
                <div className="v"><CountUp value={metric(cat, k, total)} format={fmt(k)} /></div>
                <div className="l">{cat.metrics[k].label}</div>
                <div className="s">{k === "taux_offre_unique" || k === "offres_moyennes" ? `sur ${format(total?.nb_marches_offres, "entier")} marchés renseignés` : "selon filtres"}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      {rows && (
        <>
          <section className="rubrique">
            <header>
              <div><div className="kicker">Territoires</div><h2>Où se concentrent les marchés et la concurrence</h2></div>
              <div className="seg" role="group" aria-label="Indicateur de la carte">
                {MAP_METRICS.map((m) => (
                  <button key={m} aria-pressed={mapMetric === m} onClick={() => setMapMetric(m)}>{cat.metrics[m].label}</button>
                ))}
              </div>
            </header>
            <div className="cols cols-main">
              <Reveal>
                <FranceMap
                  carte={base.carte} values={depValues} regionOf={regionOf} format={fmt(mapMetric)}
                  label={`Carte des départements : ${cat.metrics[mapMetric].label}${mapYear ? ` en ${mapYear}` : ""}`}
                  onSelect={(d) => setF((p) => ({ ...p, region: [regionOf(d)] }))}
                />
                <div className="filters" style={{ borderBottom: 0 }}>
                  <div className="field" style={{ flex: "3 1 220px" }}>
                    <label htmlFor="curseur">Année affichée : {mapYear ?? "toutes"}</label>
                    <input id="curseur" type="range" min={0} max={ANNEES.length} step={1}
                      value={mapYear ? ANNEES.indexOf(mapYear) + 1 : 0}
                      onChange={(e) => { setPlaying(false); const i = Number(e.target.value); setMapYear(i ? ANNEES[i - 1] : null); }}
                      aria-valuetext={mapYear ? String(mapYear) : "toutes les années"} />
                  </div>
                  <button className="btn ghost" onClick={() => setPlaying(true)} disabled={playing}>Rejouer 2021 → 2026</button>
                </div>
                <p className="source">Département de l'acheteur. Cliquer un département filtre sa région. Ratios de concurrence masqués sous {MIN_OFFRES} marchés renseignés. DOM : voir tableau.</p>
              </Reveal>
              <div>
                <div className="cartouche" style={{ marginTop: 10 }}>
                  <span className="cartouche-title">Légende</span>
                  <p className="small" style={{ margin: 0 }}><b>{cat.metrics[mapMetric].label}.</b> {cat.metrics[mapMetric].definition}</p>
                </div>
                <div className="panel" style={{ marginTop: 22 }}>
                  <h3>Départements les plus élevés</h3>
                  <ol className="list-plain small">
                    {Object.entries(depValues).filter(([, v]) => v != null).sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0)).slice(0, 8).map(([c, v]) => (
                      <li key={c} style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                        <span>{base.carte.departements[c].nom} <span className="mono muted">({c})</span></span>
                        <span className="mono">{fmt(mapMetric)(v!)}</span>
                      </li>
                    ))}
                  </ol>
                  <DataTable caption="Valeurs par département" headers={["Département", cat.metrics[mapMetric].label]}
                    rows={[...byDep.entries()].sort((a, b) => a[0].localeCompare(b[0])).map(([c, s]) => [c, fmt(mapMetric)(metric(cat, mapMetric, s) ?? NaN)])} />
                </div>
              </div>
            </div>
          </section>

          <section className="rubrique">
            <header>
              <div><div className="kicker">Évolution</div><h2>Six années d'attributions</h2></div>
              <p>Les filtres s'appliquent, sauf l'année. À partir de 2024, la publication centralisée (PES Marché) rend le nombre d'offres renseigné pour plus de 80 % des marchés, contre moins de 26 % avant : les comparaisons de concurrence avant/après 2024 sont fragiles.</p>
            </header>
            <div className="cols cols-3 col-rule">
              <Reveal className="panel">
                <h3>Nombre de marchés</h3>
                <Chart label="Nombre de marchés par année" deps={[byYear]} build={(t) => vbar(t, years.map((y) => ({ label: y.label, value: metric(cat, "nombre_marches", y.s) })), fmt("nombre_marches"))} />
                <DataTable caption="Nombre de marchés par année" headers={["Année", "Marchés"]} rows={years.map((y) => [y.label, fmt("nombre_marches")(metric(cat, "nombre_marches", y.s) ?? NaN)])} />
              </Reveal>
              <Reveal className="panel" delay={0.08}>
                <h3>Montant attribué</h3>
                <Chart label="Montant attribué par année" deps={[byYear]} build={(t) => vbar(t, years.map((y) => ({ label: y.label, value: metric(cat, "montant_total", y.s) })), fmt("montant_total"), t.viz1)} />
                <DataTable caption="Montant par année" headers={["Année", "Montant"]} rows={years.map((y) => [y.label, fmt("montant_total")(metric(cat, "montant_total", y.s) ?? NaN)])} />
              </Reveal>
              <Reveal className="panel" delay={0.16}>
                <h3>Taux de marchés à offre unique</h3>
                <Chart label="Taux d'offre unique par année" deps={[byYear]} build={(t) => line(t, years.map((y) => ({ label: y.label, value: metric(cat, "taux_offre_unique", y.s) })), fmt("taux_offre_unique"), t.single, "2024")} />
                <DataTable caption="Offre unique par année" headers={["Année", "Offre unique", "Renseignement"]} rows={years.map((y) => [y.label, fmt("taux_offre_unique")(metric(cat, "taux_offre_unique", y.s) ?? NaN), format(metric(cat, "taux_renseignement_offres", y.s), "pourcentage")])} />
              </Reveal>
            </div>
            <p className="source">2026 : année partielle (données jusqu'au {base.meta.decp.date_max_notification}). Montants = montants déclarés à l'attribution ; pour un accord-cadre, il s'agit d'un plafond.</p>
          </section>

          <section className="rubrique">
            <header>
              <div><div className="kicker">Secteurs</div><h2>Ce qu'achètent les acheteurs publics, et à qui</h2></div>
            </header>
            <div className="cols cols-2 col-rule">
              <Reveal className="panel">
                <h3>Divisions CPV : nombre de marchés</h3>
                <p className="small muted">CPV : nomenclature européenne des achats publics. Douze premières divisions.</p>
                <Chart className="chart tall" label="Nombre de marchés par division CPV" deps={[byDiv]} build={(t) => hbar(t, divTop, fmt("nombre_marches"))} />
                <DataTable caption="Divisions CPV" headers={["Division", "Marchés"]} rows={divTop.map((d) => [d.label, fmt("nombre_marches")(d.value!)])} />
              </Reveal>
              <Reveal className="panel" delay={0.08}>
                <h3>Où la concurrence est la plus faible</h3>
                <p className="small muted">Taux de marchés à offre unique par division, 2024 et après, divisions comptant au moins 200 marchés renseignés.</p>
                <Chart className="chart tall" label="Taux d'offre unique par division CPV" deps={[byDiv24]} build={(t) => hbar(t, divUnique, fmt("taux_offre_unique"), t.single)} />
                <DataTable caption="Offre unique par division" headers={["Division", "Offre unique"]} rows={divUnique.map((d) => [d.label, fmt("taux_offre_unique")(d.value!)])} />
              </Reveal>
            </div>
          </section>

          <section className="rubrique">
            <header>
              <div><div className="kicker">Accès des PME</div><h2>La part des PME selon le secteur et la procédure</h2></div>
              <p>Part des marchés attribués à des PME (catégorie INSEE), parmi les titulaires de catégorie connue ; un marché à plusieurs titulaires est partagé entre eux.</p>
            </header>
            <div className="cols cols-2 col-rule">
              <Reveal className="panel">
                <h3>Part des PME par division</h3>
                <Chart className="chart tall" label="Part des PME par division CPV" deps={[byDiv]} build={(t) => hbar(t, divPme, fmt("part_pme_nombre"), t.viz2)} />
                <DataTable caption="Part PME par division" headers={["Division", "Part PME"]} rows={divPme.map((d) => [d.label, fmt("part_pme_nombre")(d.value!)])} />
              </Reveal>
              <Reveal className="panel" delay={0.08}>
                <h3>Procédures</h3>
                <Chart className="chart tall" label="Nombre de marchés par procédure" deps={[byProc]} build={(t) => hbar(t, proc, fmt("nombre_marches"))} />
                <DataTable caption="Procédures" headers={["Procédure", "Marchés", "Part PME"]} rows={[...byProc.entries()].map(([k, s]) => [procLabel.get(k) ?? k, fmt("nombre_marches")(metric(cat, "nombre_marches", s)!), fmt("part_pme_nombre")(metric(cat, "part_pme_nombre", s) ?? NaN)])} />
              </Reveal>
              <Reveal className="panel" delay={0.16} >
                <h3>Types d'acheteurs</h3>
                <Chart className="chart tall" label="Nombre de marchés par type d'acheteur" deps={[byAch]} build={(t) => hbar(t, ach, fmt("nombre_marches"))} />
                <DataTable caption="Types d'acheteurs" headers={["Type", "Marchés", "Part PME"]} rows={[...byAch.entries()].map(([k, s]) => [k, fmt("nombre_marches")(metric(cat, "nombre_marches", s)!), fmt("part_pme_nombre")(metric(cat, "part_pme_nombre", s) ?? NaN)])} />
              </Reveal>
            </div>
          </section>

          {na && (
            <section className="rubrique">
              <header>
                <div><div className="kicker">Indicateurs non additifs</div><h2>Montant médian et concentration</h2></div>
                <p>La médiane et l'indice HHI ne s'additionnent pas d'un sous-ensemble à l'autre : ils sont calculés dans l'entrepôt, au niveau national, et ne suivent pas les filtres ci-dessus.</p>
              </header>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Année</th><th className="r">Montant médian</th><th className="r">HHI titulaires</th><th className="r">Acheteurs</th><th className="r">Titulaires</th></tr></thead>
                  <tbody>
                    {na.annee.map((r) => (
                      <tr key={r.annee}><td className="mono">{r.annee}</td><td className="r">{format(r.montant_median, "euros")}</td><td className="r">{format(r.hhi_titulaires, "decimal")}</td><td className="r">{format(r.nb_acheteurs, "entier")}</td><td className="r">{format(r.nb_titulaires, "entier")}</td></tr>
                    ))}
                    <tr><td><b>2021 → 2026</b></td><td className="r"><b>{format(na.national.montant_median, "euros")}</b></td><td className="r"><b>{format(na.national.hhi_titulaires, "decimal")}</b></td><td className="r"><b>{format(na.national.nb_acheteurs, "entier")}</b></td><td className="r"><b>{format(na.national.nb_titulaires, "entier")}</b></td></tr>
                  </tbody>
                </table>
              </div>
              <p className="source">HHI : somme des carrés des parts de marché des titulaires (en %), de 0 à 10 000. Au niveau national, le marché est très peu concentré ; la concentration se lit plutôt par acheteur (voir les fiches).</p>
            </section>
          )}
        </>
      )}
    </div>
  );
}
