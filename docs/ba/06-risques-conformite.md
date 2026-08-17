# Risques, RGPD et AI Act

## Registre des risques

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| Qualité des DECP (doublons, montants aberrants) | Élevée | Élevé | Règles de nettoyage tracées, 72 tests dbt, [rapport de qualité](../qualite-donnees.md) |
| Rupture de série en 2024 (nouveau format, PES Marché) | Certaine | Moyen | Indicateurs de concurrence affichés surtout sur 2024+ ; avertissement visible |
| Codes CPV erronés dans les avis | Élevée | Moyen | Score hybride (texte + CPV) ; évaluation qui mesure ce bruit |
| Classement jugé opaque | Moyenne | Élevé | Décomposition du score affichée pour chaque avis |
| Sur-confiance dans le score | Moyenne | Élevé | Mention « aide au tri » ; avis officiel en lien ; décision humaine |
| Données personnelles des titulaires | Certaine | Élevé | Masquage des personnes physiques (voir RGPD) |
| Résumé LLM inexact | Moyenne | Moyen | Fonction optionnelle, étiquetée, avec renvoi à l'avis officiel |
| Indisponibilité des API publiques | Moyenne | Faible | Instantanés versionnés, réessais, cache |

## RGPD

- **Données concernées** : les DECP publient le nom et l'identifiant des titulaires. Un entrepreneur individuel est une **personne physique** : son nom est une donnée personnelle.
- **Base légale de la réutilisation** : données publiées en open data en application du code de la commande publique ; réutilisation compatible avec la finalité de transparence, sous réserve de minimisation.
- **Mesures appliquées**
  - Le nom d'un titulaire n'est affiché que si l'on sait qu'il s'agit d'une personne morale (SIRENE hors catégorie juridique 1000, catégorie ETI ou GE, ou forme sociale explicite) : colonne `nom_publiable` de `dim_titulaire`, testée par dbt.
  - Les entrepreneurs individuels détectés via SIRENE ne sont versionnés que par leur SIREN et un indicateur, jamais par leur nom.
  - Les contacts des avis BOAMP (noms, téléphones, e-mails) ne sont pas extraits.
  - Aucune donnée sur les utilisateurs n'est collectée par la démo (pas de compte, pas de traceur).

## AI Act (règlement (UE) 2024/1689)

| Question | Analyse |
|---|---|
| Le système est-il interdit (art. 5) ? | Non. |
| Est-il à haut risque (annexe III) ? | Non : il ne relève ni de l'emploi, ni de l'accès aux services essentiels, ni des autres domaines listés. Il aide une entreprise à trier des annonces publiques. |
| Obligations applicables | Transparence (art. 50) pour le résumé LLM : texte étiqueté comme généré, modèle nommé. Bonnes pratiques volontaires pour le reste. |
| Mesures prises | Score explicable, décision humaine, évaluation publiée avec ses limites, journal des décisions. |

La qualification est celle d'un système d'IA à **risque limité**. Elle devra être revue si le produit évolue vers une décision automatisée (dépôt d'offres sans validation humaine, par exemple).
