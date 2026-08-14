import json

from radar.boamp import _dep, eforms_criteres, parse_donnees

EFORMS = {
    "EFORMS": {
        "ContractNotice": {
            "ext:UBLExtensions": {
                "ext:UBLExtension": {
                    "ext:ExtensionContent": {
                        "efext:EformsExtension": {
                            "efac:Organizations": {
                                "efac:Organization": {
                                    "efac:Company": {
                                        "cac:PartyLegalEntity": {"cbc:CompanyID": "21750001600019"},
                                        "cac:Contact": {
                                            "cbc:Name": "Mme Exemple",
                                            "cbc:ElectronicMail": "exemple@ville.fr",
                                        },
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "cac:ProcurementProject": {
                "cbc:Description": {"#text": "Nettoyage des locaux administratifs de la ville"},
                "cac:RequestedTenderTotal": {"cbc:EstimatedOverallContractAmount": {"#text": "250000.00"}},
                "cac:MainCommodityClassification": {"cbc:ItemClassificationCode": {"#text": "90911200"}},
            },
            "cac:ProcurementProjectLot": [
                {
                    "cbc:ID": {"#text": "LOT-0001"},
                    "cac:TenderingTerms": {
                        "cac:AwardingTerms": {
                            "cac:AwardingCriterion": {
                                "cac:SubordinateAwardingCriterion": [
                                    {
                                        "ext:UBLExtensions": {
                                            "ext:UBLExtension": {
                                                "ext:ExtensionContent": {
                                                    "efext:EformsExtension": {
                                                        "efac:AwardCriterionParameter": {"efbc:ParameterNumeric": "40"}
                                                    }
                                                }
                                            }
                                        },
                                        "cbc:AwardingCriterionTypeCode": {"#text": "price"},
                                        "cbc:Description": {"#text": "Prix"},
                                    },
                                    {
                                        "ext:UBLExtensions": {
                                            "ext:UBLExtension": {
                                                "ext:ExtensionContent": {
                                                    "efext:EformsExtension": {
                                                        "efac:AwardCriterionParameter": {"efbc:ParameterNumeric": "60"}
                                                    }
                                                }
                                            }
                                        },
                                        "cbc:AwardingCriterionTypeCode": {"#text": "quality"},
                                        "cbc:Description": {"#text": "Valeur technique"},
                                    },
                                ]
                            }
                        }
                    },
                },
                {"cbc:ID": {"#text": "LOT-0002"}},
            ],
        }
    }
}

FNS = {
    "FNSimple": {
        "organisme": {"codeIdentificationNational": "21950063400395"},
        "initial": {
            "procedure": {"criteresAttrib": "Prix : 70 % ; Valeur technique : 30 %"},
            "natureMarche": {
                "codeCPV": {"objetPrincipal": {"classPrincipale": "39221000"}},
                "description": "Achat d'équipements de cuisine issus du réemploi",
                "dureeMois": "48",
            },
            "lots": {
                "lot": [
                    {"description": "Équipements de cuisson", "estimationValeur": {"valeur": "65000"}},
                    {"description": "Équipements réfrigérés", "estimationValeur": {"valeur": "30000"}},
                ]
            },
        },
    }
}


def test_eforms():
    d = parse_donnees(json.dumps(EFORMS))
    assert d["cpv_principal"] == "90911200"
    assert d["acheteur_siret"] == "21750001600019"
    assert d["montant_estime"] == 250000.0
    assert d["nb_lots"] == 2
    assert d["ponderation_prix"] == 40.0
    assert "Valeur technique 60 %" in d["criteres"]


def test_eforms_ne_conserve_aucune_donnee_de_contact():
    d = parse_donnees(json.dumps(EFORMS))
    assert "exemple@ville.fr" not in json.dumps(d)
    assert "Mme Exemple" not in json.dumps(d)


def test_fnsimple():
    d = parse_donnees(json.dumps(FNS))
    assert d["cpv_codes"] == ["39221000"]
    assert d["acheteur_siret"] == "21950063400395"
    assert d["montant_estime"] == 95000.0  # somme des lots, pas de montant global
    assert d["nb_lots"] == 2
    assert d["ponderation_prix"] == 70.0
    assert d["duree_mois"] == 48.0


def test_donnees_vides_ou_invalides():
    assert parse_donnees(None)["cpv_codes"] == []
    assert parse_donnees("{pas du json")["nb_lots"] == 1


def test_criteres_eforms_dedoublonnes():
    assert len(eforms_criteres(EFORMS)) == 2


def test_departements_normalises():
    assert _dep(2) == "02"
    assert _dep("2a") == "2A"
    assert _dep("971") == "971"
