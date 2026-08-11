import { Link } from "react-router-dom";

export default function Introuvable() {
  return (
    <div className="container rubrique">
      <h1>Page introuvable</h1>
      <p className="lead">Cette adresse ne correspond à aucune page du radar.</p>
      <Link className="btn" to="/">Revenir à l'étude de cas</Link>
    </div>
  );
}
