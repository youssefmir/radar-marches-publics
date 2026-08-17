# Note de cadrage — Radar Marchés Publics

| Élément | Contenu |
|---|---|
| Porteur | Youssef Mir, Business Analyst IA |
| Statut | Version 1.0 — périmètre MVP livré |
| Date | Novembre 2026 |

## 1. Contexte

La commande publique française représente plus d'un million de marchés attribués depuis 2021 dans les DECP (données essentielles de la commande publique). Les PME y sont nombreuses en nombre de marchés, mais minoritaires en montant (voir le [panorama](https://youssefmir.github.io/radar-marches-publics/#/panorama)). Depuis 2024, environ un quart des marchés dont le nombre d'offres est renseigné n'a reçu qu'une seule offre : de la concurrence potentielle reste inexploitée.

## 2. Problème

Une PME qui veut répondre à des marchés publics fait face à trois difficultés :

- **Le volume** : plusieurs milliers d'avis ouverts à tout moment, dispersés entre le BOAMP et les profils d'acheteurs.
- **Le manque de contexte** : un avis ne dit ni combien d'offres l'acheteur reçoit d'habitude, ni qui détient le marché sortant.
- **Le temps** : la veille repose sur le dirigeant ou un chargé d'affaires, qui arbitre entre veille et production.

## 3. Objectifs

| Objectif | Indicateur | Cible (hypothèse) |
|---|---|---|
| Réduire le temps de veille | Heures par semaine consacrées à la veille | − 60 % |
| Mieux cibler | Part des avis consultés jugés pertinents | ≥ 50 % dans les 10 premiers |
| Répondre davantage | Nombre de réponses déposées par an | + 50 % |
| Gagner plus | Taux de succès des réponses | stable ou en hausse |

Les cibles sont des hypothèses de cadrage, à valider par un pilote (voir [KPI et business case](05-kpi-business-case.md)).

## 4. Périmètre

**Dans le périmètre (MVP)**

- Entrepôt de données des attributions 2021 → 2026 (DECP), nettoyé, testé, documenté.
- Couche sémantique des indicateurs (source unique des chiffres).
- Panorama de la commande publique (BI) et fiches acheteur.
- Radar AO : classement expliqué des avis BOAMP ouverts pour un profil d'entreprise, grille go/no-go.
- Évaluation reproductible du moteur de recherche.
- Démo statique (trois profils fictifs) et application locale (profil personnalisé, rafraîchissement BOAMP).

**Hors périmètre**

- Rédaction automatique des réponses (mémoire technique) : risque juridique et de qualité trop élevé pour un MVP.
- Collecte des avis des profils d'acheteurs non publiés au BOAMP.
- Alertes par e-mail et comptes utilisateurs.

## 5. Parties prenantes

| Partie prenante | Attente | Implication |
|---|---|---|
| Dirigeant de PME | Gagner du temps, décider vite | Utilisateur principal, valide la grille go/no-go |
| Chargé d'affaires | Une liste courte et argumentée | Utilisateur quotidien |
| Acheteurs publics | Plus de candidats, de meilleure qualité | Bénéficiaires indirects |
| Fournisseurs de données (DILA, decp.info, INSEE) | Réutilisation conforme | Licences respectées, sources citées |

## 6. Contraintes et hypothèses

- Données exclusivement ouvertes (Licence Ouverte 2.0, CC BY 4.0 pour la CPV).
- Exécution sur un poste standard (CPU), sans clé d'API obligatoire.
- RGPD : certains titulaires sont des personnes physiques (entrepreneurs individuels).
- AI Act : système d'aide à la décision transparent, sans décision automatisée.

## 7. Livrables

Voir le [sommaire des livrables](../README.md).
