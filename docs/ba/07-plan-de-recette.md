# Plan de recette

## Stratégie

| Niveau | Outil | Ce qui est vérifié | Commande |
|---|---|---|---|
| Données | dbt (72 tests) | Unicité, non-nullité, intégrité référentielle, valeurs acceptées, conservation des montants, bornes | `make dbt` |
| Pipeline et IA | pytest | Parseur BOAMP multi-schéma, composantes du score, go/no-go, métriques d'évaluation, couche sémantique, API, absence de sortie LLM sans clé | `make test` |
| Front | Vitest | Agrégation du cube, ratios, classes de la carte, formats français | `make test` |
| Interface | Playwright | Rendu des pages clés (clair/sombre, ordinateur/mobile), absence d'erreur console | `make screenshots` |
| Qualité de la recherche | Évaluation hors ligne | Précision@10, nDCG@10, rappel@50 sur échantillon de test | `make evaluate` |

## Cas de recette fonctionnelle

| ID | Scénario | Résultat attendu | Statut |
|---|---|---|---|
| R1 | Ouvrir la démo, page d'accueil | Chiffres réels, carte animée, dates des sources visibles | OK |
| R2 | Radar, profil Ardoise Bâtiment | 30 avis, scores décroissants, mention « Profil fictif » | OK |
| R3 | Ouvrir l'analyse d'un avis | Grille go/no-go, historique, décomposition = score | OK |
| R4 | Panorama, filtre région + division | Tous les blocs cohérents | OK |
| R5 | Fiche d'un acheteur | Titulaires : noms masqués si personne physique possible | OK |
| R6 | Thème sombre puis clair | Bascule immédiate, contrastes lisibles | OK |
| R7 | Mobile 390 px | Pas de défilement horizontal | OK |
| R8 | Application locale, profil personnalisé | Classement recalculé | OK |
| R9 | Résumé LLM sans clé | Message « désactivé », aucun texte inventé | OK |
| R10 | Adresse inconnue | Page « introuvable », pas d'erreur 404 de l'hébergeur | OK |

## Critères de sortie

- 100 % des tests automatisés au vert.
- Aucun chiffre affiché sans source (couche sémantique ou hypothèse étiquetée).
- Captures à jour dans `docs/img/`.
