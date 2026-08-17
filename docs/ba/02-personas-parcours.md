# Personas et parcours utilisateur

Les personas sont des **archétypes construits** à partir de la littérature sur l'accès des PME à la commande publique et des données DECP. Ils ne décrivent pas des personnes réelles et restent à confronter à des entretiens.

## Persona 1 — Claire, dirigeante de PME du BTP

| | |
|---|---|
| Entreprise | PME de gros œuvre et de rénovation, 80 salariés, Île-de-France (type « Ardoise Bâtiment », fictive) |
| Rôle | Dirigeante, décide seule des réponses aux appels d'offres |
| Objectif | Remplir le carnet de commandes à 6 mois avec des chantiers rentables |
| Frustrations | Passe ses soirées sur le BOAMP ; découvre trop tard les avis pertinents ; perd des appels d'offres face à un titulaire installé |
| Ce qu'elle attend | Une liste courte, chaque matin, avec une raison claire de répondre ou non |
| Citation (illustrative) | « Je ne veux pas plus d'avis, je veux les bons. » |

## Persona 2 — Karim, chargé d'affaires dans une ESN

| | |
|---|---|
| Entreprise | ESN data et BI, 40 salariés, Lyon (type « Analytica Seine », fictive) |
| Rôle | Chargé d'affaires, prépare les dossiers de candidature |
| Objectif | Qualifier vite et argumenter la décision auprès de la direction |
| Frustrations | Les codes CPV des avis sont approximatifs ; aucun historique de l'acheteur sous la main |
| Ce qu'il attend | Le contexte de l'acheteur (offres reçues, titulaires, montants) à côté de l'avis |
| Citation (illustrative) | « Si l'acheteur reçoit douze offres à chaque fois, je veux le savoir avant de passer trois jours sur le mémoire. » |

## Parcours utilisateur (TO-BE)

| Étape | Action | Écran | Émotion visée |
|---|---|---|---|
| 1. Définir son profil | Décrire l'activité, choisir CPV, départements, fourchette | Radar — profil | Simple, une seule fois |
| 2. Lire le classement | Parcourir les 30 premiers avis, score et verdict | Radar — classement | Clarté |
| 3. Comprendre un score | Ouvrir l'analyse : décomposition, go/no-go | Radar — analyse | Confiance |
| 4. Vérifier l'acheteur | Ouvrir la fiche : historique, concurrence, titulaires | Fiches acheteur | Lucidité |
| 5. Décider | Go / no-go, motif noté | Hors outil (MVP) | Maîtrise |
| 6. Prendre du recul | Comparer secteurs et territoires | Panorama | Vision stratégique |

## Moments de vérité

- **Le premier classement** : s'il n'affiche pas d'avis manifestement pertinents dans les 10 premiers, l'utilisateur abandonne. D'où l'évaluation chiffrée de la précision@10.
- **L'explication** : un score sans justification n'est pas actionnable. Chaque résultat affiche sa décomposition et ses sources.
