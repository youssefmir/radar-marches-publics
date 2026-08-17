"""Moteur de la couche sémantique : compile les métriques YAML en SQL DuckDB.

Exemple :
    sem = Semantic.load()
    sem.query(["nombre_marches", "taux_offre_unique"], by=["annee"], where={"region": "11"})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import duckdb
import pandas as pd
import yaml

from . import config

FROM = """
from main.fct_attributions f
join main.dim_cpv c on c.code_cpv = f.code_cpv
join main.dim_geo g on g.code_departement = f.departement_code
join main.dim_acheteur a on a.acheteur_id = f.acheteur_id
"""


@dataclass
class Semantic:
    spec: dict[str, Any]
    con: duckdb.DuckDBPyConnection

    @classmethod
    def load(cls, con: duckdb.DuckDBPyConnection | None = None) -> Semantic:
        spec = yaml.safe_load(config.SEMANTIC.read_text())
        con = con or duckdb.connect(str(config.WAREHOUSE), read_only=True)
        return cls(spec, con)

    # -- compilation -------------------------------------------------------------------------
    def _where(self, where: dict[str, Any] | None) -> tuple[str, list[Any]]:
        if not where:
            return "", []
        parts, params = [], []
        for dim, val in where.items():
            col = self.spec["dimensions"][dim]["sql"]
            if isinstance(val, list | tuple | set):
                parts.append(f"{col} in ({', '.join('?' for _ in val)})")
                params += list(val)
            else:
                parts.append(f"{col} = ?")
                params.append(val)
        return "where " + " and ".join(parts), params

    def measures_sql(self, names: list[str] | None = None) -> str:
        ms = self.spec["measures"]
        return ",\n    ".join(f"{ms[n]['sql']} as {n}" for n in (names or ms))

    def query(self, metrics: list[str], by: list[str] | None = None, where: dict | None = None) -> pd.DataFrame:
        by = by or []
        dims = self.spec["dimensions"]
        sel_dims = [f"{dims[d]['sql']} as {d}" for d in by]
        w, params = self._where(where)
        group = f"group by {', '.join(str(i + 1) for i in range(len(by)))}" if by else ""
        base = self.con.execute(f"select {', '.join(sel_dims + [self.measures_sql()])} {FROM} {w} {group}", params).df()
        out = base[by].copy() if by else pd.DataFrame(index=base.index)
        for m in metrics:
            spec = self.spec["metrics"][m]
            if spec["type"] == "ratio":
                num = base[spec["numerator"]].astype(float)
                out[m] = num / base[spec["denominator"]].astype(float) if spec.get("denominator") else num
            else:
                extra = self._sql_metric(m, by, where)
                out = out.merge(extra, on=by, how="left") if by else out.assign(**{m: extra[m].iat[0]})
        return out

    def _sql_metric(self, m: str, by: list[str], where: dict | None) -> pd.DataFrame:
        spec = self.spec["metrics"][m]
        dims = self.spec["dimensions"]
        w, params = self._where(where)
        sel = [f"{dims[d]['sql']} as {d}" for d in by]
        gb = ", ".join(d for d in by)
        if spec["grain"] == "attribution":
            sql = f"select {', '.join(sel + [spec['sql'] + ' as ' + m])} {FROM} {w}"
            sql += f" group by {', '.join(str(i + 1) for i in range(len(by)))}" if by else ""
        elif spec["grain"] == "marche":
            sel_m = [f"any_value({dims[d]['sql']}) as {d}" for d in by]
            inner = f"select f.marche_uid, {', '.join(sel_m + ['any_value(f.montant_marche) as montant_marche'])} {FROM} {w} group by f.marche_uid"
            sql = f"select {', '.join(by + [spec['sql'] + ' as ' + m])} from ({inner})"
            sql += f" group by {gb}" if by else ""
        elif spec["grain"] == "hhi":
            inner = (
                f"select {', '.join(sel + ['f.titulaire_key', 'sum(f.montant_part) as mt'])} {FROM} {w}"
                f" {'and' if w else 'where'} f.titulaire_key <> 'INCONNU' and f.montant_part is not null"
                f" group by {', '.join([str(i + 1) for i in range(len(by))] + ['f.titulaire_key'])}"
            )
            part = f"100.0 * mt / sum(mt) over ({'partition by ' + gb if by else ''})"
            sql = f"select {', '.join(by + [f'sum(power(p, 2)) as {m}'])} from (select *, {part} as p from ({inner}))"
            sql += f" group by {gb}" if by else ""
        else:
            raise ValueError(f"grain inconnu : {spec['grain']}")
        return self.con.execute(sql, params).df()

    def cube(self, by: list[str]) -> pd.DataFrame:
        """Agrégats additifs (mesures brutes) pour un filtrage côté navigateur."""
        dims = self.spec["dimensions"]
        sel = [f"{dims[d]['sql']} as {d}" for d in by]
        sql = f"select {', '.join(sel + [self.measures_sql()])} {FROM} group by {', '.join(str(i + 1) for i in range(len(by)))}"
        return self.con.execute(sql).df()

    def catalog(self) -> dict[str, Any]:
        """Définitions exportées vers le site (libellés, formules, glossaire)."""
        return {
            "periode": self.spec["periode"],
            "dimensions": {k: v["label"] for k, v in self.spec["dimensions"].items()},
            "measures": {k: v["label"] for k, v in self.spec["measures"].items()},
            "metrics": {
                k: {kk: vv for kk, vv in v.items() if kk != "sql"} | {"definition": " ".join(v["definition"].split())}
                for k, v in self.spec["metrics"].items()
            },
        }
