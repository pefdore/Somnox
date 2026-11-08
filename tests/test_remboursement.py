from somnox.analysis import analyse
from somnox.models import ClinicalContext, PolygraphData


def _data(iah=20.0, **kw):
    return PolygraphData(iah=iah, temps_analyse_min=420, spo2_minimale=90, index_desat=iah, **kw)


def test_ppc_severe_sans_comorbidites():
    r = analyse(_data(iah=35), ClinicalContext())
    assert "PPC" in r.proposition_therapeutique and "30" in r.proposition_therapeutique


def test_ppc_moderee_avec_comorbidites():
    r = analyse(_data(iah=20), ClinicalContext(comorbidites=["HTA"]))
    assert "PPC" in r.proposition_therapeutique and "comorbidités" in r.proposition_therapeutique


def test_oam_moderee_sans_comorbidites():
    r = analyse(_data(iah=20), ClinicalContext())
    assert "OAM" in r.proposition_therapeutique


def test_oam_si_refus_ppc():
    r = analyse(_data(iah=20), ClinicalContext(comorbidites=["diabète"], refus_ppc=True))
    assert "OAM" in r.proposition_therapeutique and "refusant" in r.proposition_therapeutique


def test_pas_de_remboursement_leger():
    r = analyse(_data(iah=8), ClinicalContext())
    assert "Pas d'indication de remboursement" in r.proposition_therapeutique


def test_arrete_variantes():
    r = analyse(_data(iah=20), ClinicalContext(epworth=6, boss=1))
    assert "n'a pas de somnolence" in r.rappel_arrete and "BOSS à 1" in r.rappel_arrete
    r = analyse(_data(iah=20), ClinicalContext(epworth=15))
    assert "notifié de l'arrêté" in r.rappel_arrete
    r = analyse(_data(iah=20), ClinicalContext(boss=5))
    assert "notifié de l'arrêté" in r.rappel_arrete


def test_vigilance_boss_manquant():
    r = analyse(_data(iah=20), ClinicalContext())
    assert any("BOSS" in v["texte"] for v in r.vigilance) or any("BOSS" in c for c in r.checklist)


def test_memo_contient_vigilance():
    from pathlib import Path

    from somnox.generate import render
    from somnox.parser import parse_text

    d = parse_text((Path(__file__).parent / "samples" / "noxt3s_sample.txt").read_text(encoding="utf-8"))
    r = analyse(d, ClinicalContext(epworth=8, boss=1, comorbidites=["HTA"]))
    memo = render("memo", d, r)
    assert "POINTS DE VIGILANCE" in memo
    assert "Immédiat" in memo
    conclusion = render("compte_rendu", d, r)
    assert "SAHOS" in conclusion and "IAH 47.3/h" in conclusion.replace(",", ".")
    assert "arrêté révisé du 28 mars 2022" in conclusion
