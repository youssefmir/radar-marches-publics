# Rapport de qualité des données DECP

> Généré par `make quality` (`python -m radar.quality`) à partir de l'entrepôt DuckDB. Ne pas modifier à la main.

- Source : [DECP consolidées – decp.info](https://www.data.gouv.fr/datasets/donnees-essentielles-de-la-commande-publique-consolidees-format-tabulaire) (Licence Ouverte 2.0), ressource du 2026-10-31, SHA-256 `24b6b5773d19e388…`
- Lignes du fichier source : **3 361 764** (marché × titulaire × modification)
- Dernière date de notification retenue : 2026-10-31

## Entonnoir de nettoyage (lignes marché × titulaire)

| Étape | Lignes |
|---|---:|
| Attributions initiales publiées (toutes dates) | 2 141 902 |
| R1 – hors période 2021→aujourd'hui ou date absente | -379 903 |
| R1b – acheteur non identifié | -6 |
| **Périmètre analysé** | **1 761 993** |
| R2 – doublons exacts (même marché, même titulaire) | -3 123 |
| R2b – quasi-doublons (même acheteur, objet, montant, date, titulaire) | -267 329 |
| **Attributions retenues (fct_attributions)** | **1 491 541** |

R2c – accords-cadres multi-attributaires publiés avec un identifiant par titulaire : 1 329 760 identifiants → **1 264 104 marchés** (65 656 identifiants fusionnés).

## Montants (règle R3)

| Statut | Lignes | Part |
|---|---:|---:|
| ok | 1 424 637 | 95,5 % |
| absent | 35 423 | 2,4 % |
| nul_ou_negatif | 25 603 | 1,7 % |
| aberrant | 5 690 | 0,4 % |
| valeur_remplissage | 188 | 0,0 % |

Les montants classés « suspects » par decp.info (comparaison aux marchés similaires) sont **conservés** : 24 628 lignes, 36,6 % du montant total retenu. Ils correspondent surtout à des plafonds d'accords-cadres élevés. Les montants « aberrants » sont exclus des sommes (le marché reste compté).

## Nombre d'offres (règle R4)

| Statut | Lignes | Part |
|---|---:|---:|
| ok | 787 076 | 52,8 % |
| absent | 696 236 | 46,7 % |
| hors_seuil | 5 113 | 0,3 % |
| zero | 3 116 | 0,2 % |

## Identifiants (règle R5, contrôle de Luhn)

- SIRET acheteur valide : 99,9 %
- Titulaires identifiés par un SIRET : 95,0 % ; dont SIRET invalide (clé de Luhn) : 16 012 lignes

## Complétude des champs clés

| Champ | Taux |
|---|---:|
| code_cpv | 100,0 % |
| code_cpv_dans_nomenclature | 99,3 % |
| procedure | 92,8 % |
| montant_exploitable | 95,5 % |
| offres_exploitables | 52,8 % |
| categorie_titulaire | 92,1 % |
| objet | 99,6 % |
| duree_mois | 99,4 % |
| departement_acheteur | 99,2 % |

## Rupture de 2024

Depuis le 1er janvier 2024 (arrêtés du 22 décembre 2022), les données essentielles suivent un nouveau format et sont centralisées via le PES Marché. Le nombre de marchés publiés augmente nettement : les évolutions 2023 → 2024 mesurent autant l'amélioration de la publication que l'activité réelle.

| Année | Lignes | Part issue du PES Marché 2024 | Nb d'offres exploitable |
|---|---:|---:|---:|
| 2021 | 222 527 | 1,5 % | 17,9 % |
| 2022 | 243 703 | 4,7 % | 19,0 % |
| 2023 | 251 496 | 7,7 % | 25,1 % |
| 2024 | 319 564 | 35,4 % | 82,0 % |
| 2025 | 287 771 | 42,3 % | 84,4 % |
| 2026 | 166 480 | 42,2 % | 79,8 % |

## Enrichissement SIRENE

- Titulaires enrichis par l'API Recherche d'entreprises : 13 451 sur 187 918 (les plus importants en montant), couvrant 73,5 % du montant attribué.
- Entrepreneurs individuels détectés (noms masqués dans tous les exports) : 18.
- Pour les autres titulaires, la catégorie d'entreprise provient de l'enrichissement SIRENE réalisé par decp.info.
