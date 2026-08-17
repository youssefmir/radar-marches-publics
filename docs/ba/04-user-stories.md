# User stories, critères d'acceptation et priorisation MVP

Format INVEST : indépendante, négociable, valorisable, estimable, petite, testable. Priorisation MoSCoW pour le MVP. Chaque critère Gherkin est couvert par un test automatisé ou par le [plan de recette](07-plan-de-recette.md).

## Synthèse MoSCoW

| ID | User story (résumé) | MoSCoW | Statut |
|---|---|---|---|
| US1 | Classer les avis ouverts pour mon profil | Must | Livré |
| US2 | Comprendre pourquoi un avis est bien classé | Must | Livré |
| US3 | Qualifier un avis (go/no-go) | Must | Livré |
| US4 | Connaître l'historique d'un acheteur | Must | Livré |
| US5 | Explorer le panorama par secteur et territoire | Should | Livré |
| US6 | Saisir mon propre profil | Should | Livré (application locale) |
| US7 | Rafraîchir les avis en direct | Should | Livré (application locale) |
| US8 | Obtenir un résumé d'avis | Could | Livré, optionnel (clé LLM requise) |
| US9 | Recevoir une alerte quotidienne | Won't (MVP) | Piste |
| US10 | Générer le mémoire technique | Won't | Écarté (risque) |

## US1 — Classer les avis ouverts

> En tant que dirigeante de PME, je veux voir les avis ouverts classés selon mon activité, mon territoire et ma taille, afin de ne lire que ceux qui me concernent.

```gherkin
Scénario : classement d'un profil
  Étant donné un profil avec une description, des codes CPV et des départements
  Quand je lance le classement
  Alors j'obtiens au plus 30 avis triés par score décroissant
  Et chaque avis affiche sa date limite, son acheteur et ses départements
```

## US2 — Comprendre le score

> En tant que chargé d'affaires, je veux voir la décomposition du score, afin de juger si le classement est fiable.

```gherkin
Scénario : décomposition cohérente
  Étant donné un avis classé
  Quand j'ouvre son analyse
  Alors je vois les 7 composantes avec valeur, poids et points
  Et la somme des points est égale au score affiché (à l'arrondi près)
```

## US3 — Qualifier un avis

> En tant que dirigeante, je veux une grille go/no-go issue des champs structurés de l'avis, afin de décider en une minute.

```gherkin
Scénario : date limite proche
  Étant donné un avis dont la date limite est dans moins de 7 jours
  Quand j'affiche sa grille
  Alors le critère « Date limite » est marqué « risque »
  Et le verdict est « no-go probable »
```

## US4 — Historique de l'acheteur

> En tant que chargé d'affaires, je veux connaître le nombre d'offres que reçoit l'acheteur et son titulaire principal, afin d'estimer mes chances.

```gherkin
Scénario : acheteur rapproché par SIRET
  Étant donné un avis dont l'acheteur a un SIRET présent dans les DECP
  Quand j'ouvre l'analyse
  Alors je vois le nombre de marchés passés, les offres moyennes et le taux d'offre unique
  Et le nom du titulaire principal n'est affiché que s'il s'agit d'une personne morale
```

## US5 — Panorama

> En tant que dirigeante, je veux comparer secteurs et territoires, afin de choisir où concentrer mes efforts commerciaux.

```gherkin
Scénario : filtres cohérents
  Étant donné le panorama
  Quand je filtre sur une région et une division CPV
  Alors tous les chiffres clés, la carte et les graphiques reflètent le même périmètre
```

## US6 et US7 — Profil personnalisé et rafraîchissement

```gherkin
Scénario : profil personnalisé dans l'application locale
  Étant donné l'application locale lancée par « make app »
  Quand je saisis une description d'au moins 10 caractères et je valide
  Alors le classement est recalculé pour mon profil
Scénario : description trop courte
  Quand je saisis une description de moins de 10 caractères
  Alors l'API refuse la demande (erreur 422)
```

## US8 — Résumé d'avis par LLM

```gherkin
Scénario : aucune clé configurée
  Étant donné qu'aucune clé LLM n'est configurée
  Quand je demande un résumé
  Alors aucun texte n'est affiché comme résumé
  Et un message indique que la fonction est désactivée
```
