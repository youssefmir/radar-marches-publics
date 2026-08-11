// Vue tableau accessible d'un graphique (chaque valeur reste lisible sans survol).
export default function DataTable({ caption, headers, rows }: {
  caption: string; headers: string[]; rows: (string | number)[][];
}) {
  return (
    <details>
      <summary>Voir le tableau</summary>
      <div className="table-wrap">
        <table>
          <caption className="sr-only">{caption}</caption>
          <thead><tr>{headers.map((h, i) => <th key={h} className={i ? "r" : ""}>{h}</th>)}</tr></thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>{r.map((c, j) => <td key={j} className={j ? "r" : ""}>{c}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
