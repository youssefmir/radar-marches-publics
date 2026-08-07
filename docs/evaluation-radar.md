# Évaluation de la recherche du Radar AO

> Généré par `make evaluate` (`python -m radar.evaluate`). Chiffres réels, reproductibles (graine 42, partition déterministe par hachage de l'identifiant d'avis).

## Protocole

- Corpus : 7187 avis BOAMP ouverts au 2026-11-01 portant au moins un code CPV ; 2098 avis de **réglage** (30 %) et 5089 avis de **test** (70 %).
- Vérité terrain : les codes CPV saisis par les acheteurs (pertinence binaire). Elle est bruitée : un avis pertinent pour un métier peut être codé dans une autre classe.
- **Q1 « profil CPV »** : une requête par classe CPV (4 chiffres) comptant 8 à 400 avis ; texte = libellé de la classe + libellés des 3 codes de la classe les plus fréquents dans l'historique DECP. Pertinent = avis avec un code dans la classe.
- **Q2 « avis exemple »** : un avis tiré au hasard sert de requête (objet + 500 premiers caractères de la description) ; pertinent = autre avis du même groupe CPV (3 chiffres).
- Le texte indexé (objet + description) n'inclut jamais les libellés CPV ; la composante CPV du score complet est exclue, car elle lirait directement la vérité terrain.
- Réglage : alpha (poids des embeddings dans l'hybride) choisi sur l'échantillon de réglage seulement : **alpha = 0.5**.

## Résultats sur l'échantillon de test

| Jeu | Méthode | Requêtes | Precision@10 | nDCG@10 | Recall@50 |
|---|---|---:|---:|---:|---:|
| Q1 profil CPV | BM25 | 223 | 0,302 [0,267 ; 0,339] | 0,322 [0,285 ; 0,360] | 0,328 [0,300 ; 0,358] |
| Q1 profil CPV | Embeddings MiniLM | 223 | 0,153 [0,129 ; 0,179] | 0,165 [0,139 ; 0,193] | 0,175 [0,156 ; 0,194] |
| Q1 profil CPV | Embeddings e5-small | 223 | 0,168 [0,142 ; 0,196] | 0,185 [0,156 ; 0,214] | 0,194 [0,172 ; 0,216] |
| Q1 profil CPV | Hybride (alpha=0.5, réglé) | 223 | 0,313 [0,277 ; 0,348] | 0,338 [0,298 ; 0,375] | 0,345 [0,316 ; 0,374] |
| Q1 profil CPV | Hybride RRF | 223 | 0,288 [0,253 ; 0,322] | 0,311 [0,274 ; 0,346] | 0,331 [0,302 ; 0,359] |
| Q2 avis exemple | BM25 | 295 | 0,382 [0,343 ; 0,421] | 0,404 [0,366 ; 0,444] | 0,133 [0,116 ; 0,151] |
| Q2 avis exemple | Embeddings MiniLM | 295 | 0,248 [0,215 ; 0,281] | 0,263 [0,228 ; 0,296] | 0,072 [0,063 ; 0,082] |
| Q2 avis exemple | Embeddings e5-small | 295 | 0,330 [0,294 ; 0,365] | 0,358 [0,321 ; 0,393] | 0,097 [0,087 ; 0,108] |
| Q2 avis exemple | Hybride (alpha=0.5, réglé) | 295 | 0,404 [0,367 ; 0,444] | 0,427 [0,390 ; 0,467] | 0,136 [0,119 ; 0,154] |
| Q2 avis exemple | Hybride RRF | 295 | 0,398 [0,361 ; 0,437] | 0,421 [0,384 ; 0,461] | 0,135 [0,118 ; 0,151] |

Entre crochets : intervalle de confiance à 95 % par bootstrap sur les requêtes.

**Lecture.**
- Q1 profil CPV : l'hybride atteint un nDCG@10 de 0,338 contre 0,322 pour BM25 (+0,016) et 0,185 pour les embeddings seuls. Le gain sur BM25 est modeste : les intervalles de confiance se recouvrent.
- Q2 avis exemple : l'hybride atteint un nDCG@10 de 0,427 contre 0,404 pour BM25 (+0,023) et 0,358 pour les embeddings seuls. Le gain sur BM25 est modeste : les intervalles de confiance se recouvrent.

### Choix de alpha (échantillon de réglage, nDCG@10 moyen Q1 + Q2)

| alpha | 0.0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 | 1.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| nDCG@10 | 0,339 | 0,345 | 0,349 | 0,351 | 0,352 | 0,354 | 0,347 | 0,337 | 0,320 | 0,293 | 0,261 |

### Q1 par famille d'achat (hybride réglé)

| Famille | Precision@10 | nDCG@10 |
|---|---:|---:|
| Fournitures | 0,351 | 0,384 |
| Services | 0,262 | 0,285 |
| Travaux | 0,425 | 0,422 |

## Analyse d'erreurs (Q1, requêtes les moins bien servies par l'hybride)

- **0341 – Bois** (nDCG@10 = 0,000, 8 avis pertinents). Faux positifs en tête : « Traitement du bois issus des déchetteries du SMICTOM LGB (Bois de catégorie A, B et AB) » (90513000 Services de traitement et d'élimination des ordures) ; « Création d'un réseau de chaleur chaufferie bois Pont du Casse » (45251200 Travaux de construction de centrales de chauffage) ; « Accord-cadre à bons de commande pour l'assistance technique, l'entretien, la maintenance e » (50720000 Services de réparation et d'entretien de chauffage )
- **2245 – Imprimés infalsifiables** (nDCG@10 = 0,000, 10 avis pertinents). Faux positifs en tête : « Acquisition d'ouvrages imprimés français et étrangers pour l'Université d'Angers » (22110000 Livres imprimés) ; « Prestations de formations et de présentation aux examens de permis de conduire poids lourd » (80511000 Services de formation du personnel) ; « Fourniture de monographies pour le compte de l’École nationale des chartes – (ENC/PSL) » (22110000 Livres imprimés)
- **3376 – Papier hygiénique, mouchoirs, essuie-mains et serviettes de table** (nDCG@10 = 0,000, 11 avis pertinents). Faux positifs en tête : « Fourniture de produits d'entretien et d'hygiène » (39830000 Produits de nettoyage) ; « Acquisition d'articles d'hygiène et produits d'entretien » (39800000 Produits de nettoyage et produits à polir) ; « LOCATION ET ENTRETIEN DE BOBINES EN TISSU ET DE RECEPTACLES D'HYGIENE FEMININE POUR LA VIL » (90900000 Services de nettoyage et d'hygiène)
- **3152 – Lampes et appareils d'éclairage** (nDCG@10 = 0,000, 15 avis pertinents). Faux positifs en tête : « www.marches-securises.fr » (45316110 Installation de matériel d'éclairage public) ; « UPEP de Langroise - Remplacement des membranes filtrantes par des lampes UV et travaux div » (45252120 Travaux de construction d'installations de traiteme) ; « Installation et entretien de matériel d'éclairage public du port de Gennevilliers » (45241600 Installation de matériel d'éclairage portuaire)
- **3741 – Équipements de sports de plein air** (nDCG@10 = 0,000, 9 avis pertinents). Faux positifs en tête : « Location de matériels et équipements audiovisuels » (32321200 Équipement audiovisuel) ; « Fourniture de matériels pour les sports collectifs et sports de raquette et prestations as » (37450000 Équipement pour sports de plein air et sur courts) ; « LILLE NEIGE 2027 » (92330000 Services de zones récréatives)
- **5073 – Services de réparation et d'entretien de groupes de réfrigération** (nDCG@10 = 0,000, 14 avis pertinents). Faux positifs en tête : « Services de réparation et d'entretien du navire Granville pendant son arrêt technique débu » (50241100 Services de réparation de navires) ; « Refonte partielle des installations frigorifiques de la criée du port d'Erquy - Réfrigérat » (45331231 Travaux d'installation de matériel de réfrigération) ; « Entretien et réparation de divers véhicules de la flotte automobile de la ville » (50100000 Services de réparation et d'entretien de véhicules )
- **5053 – Services de réparation et d'entretien de machines** (nDCG@10 = 0,000, 26 avis pertinents). Faux positifs en tête : « Travaux entretien courant des bâtiments » (45332000 Travaux de plomberie et de pose de conduits d'évacu) ; « Entretien et réparation de divers véhicules de la flotte automobile de la ville » (50100000 Services de réparation et d'entretien de véhicules ) ; « Services de réparation et d'entretien du navire Granville pendant son arrêt technique débu » (50241100 Services de réparation de navires)
- **5061 – Services de réparation et d'entretien du matériel de sécurité** (nDCG@10 = 0,000, 22 avis pertinents). Faux positifs en tête : « Services de réparation et d'entretien du navire Granville pendant son arrêt technique débu » (50241100 Services de réparation de navires) ; « Fourniture et livraison de produits et de matériels d'entretien » (39830000 Produits de nettoyage) ; « Fourniture et livraison de pièces destinées à l'entretien des réseaux d'eau potable et d'a » (44165000 Tuyaux, conduites ascendantes et manchons)

Lecture des erreurs (motifs observés dans la liste ci-dessus) :

1. **Bruit de la vérité terrain** : des avis réellement liés au besoin sont codés dans une classe voisine (produits d'hygiène codés « produits de nettoyage », éclairage codé en travaux d'installation). Une partie des « faux positifs » sont donc des résultats utiles pour une entreprise ; les métriques sont une borne basse.
2. **Polysémie et libellés courts** : « Bois » (matériau) attire les chaufferies bois et la valorisation des déchets de bois ; « réparation et entretien » attire des avis d'entretien de navires ou de véhicules. Les libellés CPV seuls sont des requêtes pauvres : d'où l'intérêt de la description libre et des codes CPV du profil.
3. **Objets non informatifs** : certains avis ont un objet réduit à une URL ou à une référence interne ; leur description, quand elle existe, porte l'essentiel du sens.
4. **Embeddings seuls en retrait** : le petit modèle multilingue (118 M de paramètres, CPU) capte mal le vocabulaire technique très spécifique des marchés, où le mot exact compte. Il apporte en revanche un gain complémentaire à BM25 dans l'hybride (synonymes, reformulations).

## Conséquences pour le produit

- Le classement final combine le texte (hybride) avec l'adéquation CPV, la géographie et la taille : l'évaluation ci-dessus mesure la seule brique texte, la plus difficile.
- Le radar est un outil d'aide au tri : il affiche la décomposition du score et ne masque aucun avis.
- Pistes : modèle d'embeddings plus grand ou affiné sur des couples (objet, CPV) issus des DECP, enrichissement des requêtes par les objets de marchés déjà gagnés par l'entreprise.
