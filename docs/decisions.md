# Journal des décisions

Chaque décision suit le format **contexte → options → choix → pourquoi**. Les chiffres cités sont reproductibles (voir les commandes du [README](../README.md)).

## D1 — Source DECP : la consolidation decp.info plutôt que les fichiers du ministère

- **Contexte** : plusieurs jeux DECP coexistent (fichiers consolidés du ministère, données par plateforme, consolidations tierces), avec un changement de format au 1er janvier 2024.
- **Options** : (a) fichiers consolidés officiels ; (b) agréger soi-même les sources ; (c) DECP consolidées et enrichies par decp.info, publiées sur data.gouv.fr.
- **Choix** : (c), version figée par empreinte SHA-256 dans `data/sources.lock.json`.
- **Pourquoi** : plus exhaustive (plus de sources agrégées), déjà au format Parquet, enrichie (catégorie d'entreprise, géographie, détection des montants anormaux), licence ouverte. Les doublons restants sont traités par nos propres règles (D3).

## D2 — Période 2021 → aujourd'hui, au grain marché × titulaire

- **Contexte** : les données remontent à 2018, mais la couverture avant 2021 est faible.
- **Options** : toute la période ; 2021+ ; 2024+ seulement.
- **Choix** : 2021+, attribution initiale (modification 0), grain marché × titulaire avec un montant réparti entre co-titulaires (`montant_part`).
- **Pourquoi** : six ans de recul suffisent pour l'historique d'un acheteur ; le grain marché × titulaire permet la part des PME et l'indice HHI sans double compte (test dbt dédié).

## D3 — Dédoublonnage par contenu

- **Contexte** : un même marché est publié par plusieurs sources sous des identifiants différents ; certains accords-cadres multi-attributaires ont un identifiant par titulaire.
- **Options** : se fier à l'identifiant `uid` ; dédoublonner par contenu.
- **Choix** : trois règles : doublons exacts (R2), quasi-doublons sur acheteur + objet + montant + date + titulaire (R2b), regroupement des multi-attributaires (R2c).
- **Pourquoi** : sans R2b, environ 470 Md€ de montants étaient comptés deux fois (mesuré au moment de la décision). Le risque inverse (fusion de deux lots identiques) est accepté et documenté.

## D4 — Montants « suspects » conservés, « aberrants » exclus

- **Contexte** : decp.info classe certains montants comme suspects ou aberrants.
- **Choix** : exclure des sommes les montants aberrants, nuls, absents ou de remplissage ; conserver les suspects ; garder le marché dans les comptes dans tous les cas.
- **Pourquoi** : les suspects ont une médiane de 4 M€ et correspondent surtout à des plafonds d'accords-cadres plausibles. Leur poids est chiffré dans le rapport de qualité pour que le lecteur juge.

## D5 — Concurrence lue surtout sur 2024+

- **Contexte** : le nombre d'offres est renseigné pour moins de 26 % des lignes avant 2024, contre plus de 80 % ensuite.
- **Choix** : indicateurs de concurrence nationaux et sectoriels mis en avant sur 2024 → 2026 ; série longue affichée avec une zone grisée d'avertissement ; ratios masqués sous 30 marchés renseignés.
- **Pourquoi** : comparer 2021 et 2025 mesurerait surtout l'amélioration de la publication.

## D6 — Couche sémantique en YAML, mesures additives + ratios

- **Contexte** : le même indicateur doit donner le même chiffre dans le README, le panorama et les fiches.
- **Options** : calculs dans le front ; outil de BI tiers ; couche sémantique maison.
- **Choix** : `semantic/metrics.yml` décrit les mesures additives et les ratios ; Python les compile en SQL, le front recalcule les ratios à partir du même cube. Médiane et HHI (non additifs) sont calculés uniquement dans l'entrepôt.
- **Pourquoi** : source unique, définitions métier lisibles par un non-développeur, test qui vérifie la cohérence cube / entrepôt.

## D7 — Cube Parquet + agrégation en JavaScript plutôt que DuckDB-WASM

- **Contexte** : le panorama doit être filtrable hors ligne sur GitHub Pages.
- **Options** : DuckDB-WASM ; agrégats précalculés figés ; cube de mesures additives lu par une petite bibliothèque Parquet.
- **Choix** : cube de 156 000 lignes (4,4 Mo), lu par hyparquet (27 Ko), agrégé en JavaScript.
- **Pourquoi** : DuckDB-WASM pèse plus de 30 Mo, au-delà du budget du dépôt ; l'additivité garantie par la couche sémantique rend un moteur SQL inutile côté navigateur.

## D8 — Score hybride expliqué plutôt qu'un modèle appris

- **Contexte** : aucune donnée de « réponse » ou de « succès » par entreprise n'est disponible pour entraîner un modèle de classement.
- **Choix** : somme pondérée de sept composantes interprétables ; poids texte réglé sur l'échantillon de réglage (alpha = 0,5), poids métier explicites pour le reste.
- **Pourquoi** : explicable, auditable, ajustable par l'utilisateur ; conforme à l'exigence de transparence. Un modèle appris deviendra pertinent une fois des décisions go/no-go journalisées.

## D9 — Modèle d'embeddings : multilingual-e5-small

- **Contexte** : recherche sémantique en français, sur CPU.
- **Options** : multilingual-e5-small ; paraphrase-multilingual-MiniLM-L12-v2 ; modèles plus grands.
- **Choix** : e5-small.
- **Pourquoi** : mesuré meilleur que MiniLM sur nos deux jeux de requêtes (nDCG@10 0,185 contre 0,165 en Q1 ; 0,358 contre 0,263 en Q2), et 4 minutes pour indexer 7 800 avis sur CPU. Seul, il reste derrière BM25 : d'où l'hybride.

## D10 — Évaluation sur la vérité terrain CPV, avec partition réglage / test

- **Contexte** : il faut des chiffres honnêtes, sans annotation manuelle.
- **Choix** : codes CPV des avis comme pertinence binaire ; 30 % des avis pour régler alpha, 70 % pour publier ; composante CPV exclue de l'évaluation ; intervalles de confiance par bootstrap.
- **Pourquoi** : reproductible et sans fuite. Limite assumée : le bruit des CPV rend les scores pessimistes ; l'analyse d'erreurs le montre.

## D11 — RGPD : noms publiés seulement pour les personnes morales avérées

- **Contexte** : des entrepreneurs individuels (personnes physiques) figurent parmi les titulaires.
- **Choix** : colonne `nom_publiable` (SIRENE hors catégorie juridique 1000, ou ETI/GE, ou forme sociale explicite) ; sinon « nom non affiché ».
- **Pourquoi** : minimisation par défaut ; mieux vaut masquer à tort une société que publier une personne.

## D12 — LLM optionnel, jamais simulé

- **Contexte** : un résumé d'avis est utile, mais aucune clé n'est disponible pour la démo.
- **Choix** : fonction présente uniquement dans l'application locale, activée par une clé fournie par l'utilisateur (Mistral ou point d'accès compatible OpenAI) ; sans clé, erreur explicite.
- **Pourquoi** : afficher un faux résumé tromperait l'utilisateur et le recruteur. Le code est testé avec un fournisseur simulé, ce qui vérifie l'intégration sans prétendre à une sortie réelle.

## D13 — Direction artistique « cartographie et bulletin officiel »

- **Contexte** : le site doit montrer le visuel propre du projet et éviter le style générique des interfaces produites en série (dégradés violets, cartes arrondies flottantes, gabarit « hero centré + trois cartes »).
- **Options** : charte « produit SaaS » neutre ; identité d'administration publique ; direction née du sujet.
- **Choix** : croiser les cartes topographiques (courbes de niveau en filigrane, cartouches de légende, échelle séquentielle sable → vert-bleu) et la typographie dense des bulletins d'annonces légales (Bitter pour les titres, Public Sans pour le texte, Spline Sans Mono pour les codes, filets et colonnes, angles vifs). Orange « balise » pour les opportunités, rouge réservé à l'offre unique.
- **Inspirations** : la clarté et l'accessibilité du GOV.UK Design System ; les cartes topographiques ; les pages d'annonces de la presse. Aucune imitation de l'identité de l'État (pas de Marianne, de bleu-blanc-rouge ni de composants du DSFR).
- **Pourquoi** : la commande publique est une affaire de territoires et d'annonces ; la forme raconte le fond. Les couleurs des graphiques sont validées par un script (luminance, saturation, séparation pour les daltonismes, contraste) en clair et en sombre ; les animations (entrée, carte révélée par région, balises, décomposition du score) durent de 150 à 600 ms, ne touchent que l'opacité et les transformations, et se désactivent avec `prefers-reduced-motion`.
