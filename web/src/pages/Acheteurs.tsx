import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchJson } from "../lib/data";
import { entier, euros, pct, decimal } from "../lib/format";
import { useAsync } from "../lib/hooks";

export interface AcheteurLigne {
  acheteur_id: string; acheteur_nom: string; acheteur_categorie: string; departement_code: string;
  nom_departement: string; nom_region: string; nb_marches: number; montant_total: number;
  part_pme: number | null; offres_moyennes: number | null; taux_offre_unique: number | null;
}

const norm = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export default function Acheteurs() {
  const { data } = useAsync<AcheteurLigne[]>(() => fetchJson("acheteurs.json"));
  const [q, setQ] = useState("");
  const [n, setN] = useState(40);
  const list = useMemo(() => {
    const t = norm(q.trim());
    return (data ?? []).filter((a) => !t || norm(`${a.acheteur_nom} ${a.nom_departement} ${a.departement_code} ${a.acheteur_id}`).includes(t));
  }, [data, q]);
  return (
    <div className="container">
      <section className="rubrique" style={{ marginTop: 28 }}>
        <header>
          <div>
            <div className="kicker">Fiches acheteur · {entier(data?.length)} acheteurs les plus actifs</div>
            <h1>Connaître l'acheteur avant de répondre</h1>
          </div>
          <p>Pour chaque acheteur : ce qu'il achète, à quel montant, combien d'offres il reçoit, qui gagne, et la place des PME. Données DECP depuis 2021.</p>
        </header>
        <div className="filters">
          <div className="field" style={{ flex: "1 1 320px" }}>
            <label htmlFor="q">Rechercher un acheteur, une ville, un département ou un SIRET</label>
            <input id="q" type="search" value={q} onChange={(e) => { setQ(e.target.value); setN(40); }} placeholder="ex. Lyon, 59, Centre hospitalier…" />
          </div>
          <span className="small muted" role="status">{entier(list.length)} résultat(s)</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Acheteur</th><th>Territoire</th><th className="r">Marchés</th><th className="r">Montant</th><th className="r">Offres moy.</th><th className="r">Offre unique</th><th className="r">Part PME</th></tr></thead>
            <tbody>
              {list.slice(0, n).map((a) => (
                <tr key={a.acheteur_id}>
                  <td><Link to={`/acheteurs/${a.acheteur_id}`}>{a.acheteur_nom}</Link><div className="small muted">{a.acheteur_categorie} · <span className="mono">{a.acheteur_id}</span></div></td>
                  <td className="small">{a.nom_departement} <span className="mono muted">({a.departement_code})</span></td>
                  <td className="r">{entier(a.nb_marches)}</td>
                  <td className="r">{euros(a.montant_total)}</td>
                  <td className="r">{decimal(a.offres_moyennes)}</td>
                  <td className="r">{pct(a.taux_offre_unique)}</td>
                  <td className="r">{pct(a.part_pme)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {list.length > n && <button className="btn ghost" style={{ marginTop: 14 }} onClick={() => setN(n + 60)}>Afficher plus</button>}
      </section>
    </div>
  );
}
