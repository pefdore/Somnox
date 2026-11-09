"""Sécurisation de l'interprétation : workflow Nox, pré/post, stades."""

from pathlib import Path

from somnox.analysis import analyse
from somnox.models import ClinicalContext, PolygraphData
from somnox.parser import parse_text

REAL = Path(__file__).parent / "samples" / "noxturnal_real.txt"


def test_checklist_cheyne_stokes_si_centrales():
    d = PolygraphData(iah=20.0, iahc=17.0, iaho=3.0, temps_analyse_min=420,
                      spo2_minimale=90, index_desat=20, cheyne_stokes_min=None)
    r = analyse(d)
    assert any("Cheyne-Stokes" in c for c in r.checklist)
    assert any("Nox Journal" in c for c in r.checklist)


def test_vigilance_stades_manquants():
    d = PolygraphData(iah=20.0, temps_analyse_min=420, spo2_minimale=90, index_desat=20,
                      duree_rem_min=None)
    r = analyse(d)
    assert any("Nox Body Sleep" in v["texte"] for v in r.vigilance)


def test_vigilance_rem_insuffisant():
    d = PolygraphData(iah=20.0, temps_analyse_min=420, spo2_minimale=90, index_desat=20,
                      duree_rem_min=18)
    r = analyse(d)
    assert any("REM insuffisant" in v["texte"] for v in r.vigilance)


def test_comparaison_pre_post_oam():
    d = parse_text(REAL.read_text(encoding="utf-8"))
    assert d.iah_pre_traitement == 19.4
    assert d.odi_pre_traitement == 18.4
    r = analyse(d, ClinicalContext(type_examen="controle_oam"))
    assert any("Comparaison pré/post-traitement" in i for i in r.interpretation)
    assert any("symptômes SOUS traitement" in c for c in r.checklist)
    assert any("Stades" not in v["texte"] for v in r.vigilance)  # stades présents dans ce rapport


def test_vigilance_valeurs_pre_manquantes():
    d = PolygraphData(iah=14.0, temps_analyse_min=420, spo2_minimale=90, index_desat=14,
                      iah_pre_traitement=None)
    r = analyse(d, ClinicalContext(type_examen="controle_oam"))
    assert any("pré-traitement non retrouvées" in v["texte"] for v in r.vigilance)


def test_variation_faible_sous_traitement():
    d = PolygraphData(iah=18.0, temps_analyse_min=420, spo2_minimale=90, index_desat=18,
                      iah_pre_traitement=19.0)
    r = analyse(d, ClinicalContext(type_examen="controle_oam"))
    assert any("Variation d'IAH faible" in v["texte"] for v in r.vigilance)


def test_stades_extraits_du_rapport_reel():
    d = parse_text(REAL.read_text(encoding="utf-8"))
    assert d.duree_rem_min == 123.0
    assert d.duree_nrem_min == 206.4
    assert d.temps_sommeil_estime_min == 329.4
