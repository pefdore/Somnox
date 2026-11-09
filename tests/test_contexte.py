from pathlib import Path

from somnox.analysis import analyse
from somnox.context import build_context
from somnox.models import ClinicalContext, PolygraphData
from somnox.parser import parse_text

PRIMO = Path(__file__).parent / "samples" / "indictions_primo.txt"
CONTROL = Path(__file__).parent / "samples" / "noxturnal_real.txt"


def test_contexte_primo():
    d = parse_text(PRIMO.read_text(encoding="utf-8"))
    ctx = build_context(d)
    assert ctx.type_examen == "primo"
    assert ctx.epworth == 13
    assert ctx.pichot == 5
    assert ctx.boss == 2
    assert ctx.ronflements_constates is True
    assert ctx.somnolence is True  # Epworth >= 10
    assert ctx.fatigue is False
    assert ctx.nycturie is False
    assert ctx.comorbidites == []
    assert "dette en sommeil" in ctx.notes


def test_contexte_controle_oam():
    d = parse_text(CONTROL.read_text(encoding="utf-8"))
    ctx = build_context(d)
    assert ctx.type_examen == "controle_oam"
    assert ctx.epworth == 6
    assert ctx.pichot == 18
    assert ctx.boss == 0


def test_comorbidites_primo_oui():
    text = PRIMO.read_text(encoding="utf-8").replace("HTA résistante : non", "HTA résistante : oui").replace("IC symptomatique : non", "IC symptomatique : oui")
    d = parse_text(text)
    ctx = build_context(d)
    assert "HTA" in ctx.comorbidites
    assert "insuffisance cardiaque" in ctx.comorbidites


def test_propositions_controle():
    # Contrôle OAM efficace (IAH < 15)
    d = PolygraphData(iah=8.0, temps_analyse_min=400, spo2_minimale=90, index_desat=8)
    r = analyse(d, ClinicalContext(type_examen="controle_oam"))
    assert "efficacité confirmée" in r.proposition_therapeutique
    assert "Poursuite de l'OAM" in r.proposition_therapeutique

    # Contrôle OAM insuffisant (IAH 15-30, avec comorbidités)
    d2 = PolygraphData(iah=20.0, temps_analyse_min=400, spo2_minimale=90, index_desat=20)
    r2 = analyse(d2, ClinicalContext(type_examen="controle_oam", comorbidites=["HTA"]))
    assert "réponse insuffisante" in r2.proposition_therapeutique
    assert "bascule vers la PPC" in r2.proposition_therapeutique

    # Contrôle OAM échec (IAH >= 30)
    r3 = analyse(PolygraphData(iah=35.0, temps_analyse_min=400, spo2_minimale=88, index_desat=35), ClinicalContext(type_examen="controle_oam"))
    assert "échec" in r3.proposition_therapeutique

    # Contrôle PPC avec IAH résiduel élevé
    r4 = analyse(PolygraphData(iah=18.0, temps_analyse_min=400, spo2_minimale=90, index_desat=18), ClinicalContext(type_examen="controle_ppc"))
    assert "réoptimisation" in r4.proposition_therapeutique


def test_type_examen_dans_documents():
    from somnox.generate import render

    d = parse_text(CONTROL.read_text(encoding="utf-8"))
    ctx = build_context(d)
    r = analyse(d, ctx)
    concl = render("compte_rendu", d, r, ctx)
    assert "Contrôle sous OAM (4 mois)" in concl
    memo = render("memo", d, r, ctx)
    assert "Type d'examen" in memo
