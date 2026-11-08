"""Tests de non-régression sur un rapport Noxturnal réel (anonymisé)."""

from pathlib import Path

import pytest

from somnox.analysis import analyse
from somnox.models import default_context
from somnox.parser import parse_text

REAL = Path(__file__).parent / "samples" / "noxturnal_real.txt"


@pytest.fixture
def data():
    return parse_text(REAL.read_text(encoding="utf-8"), source="noxturnal_real.txt")


def test_noxt3s_extraction(data):
    assert data.iah == 14.0
    assert data.iaho == 12.4
    assert data.iahc == 1.3
    assert data.index_desat == 14.7
    assert data.iah_dorsal == 71.6
    assert data.iah_latéral == 7.7
    assert data.iah_rem == 7.3
    assert data.charge_hypoxique == 20.1
    assert data.t90 == 1.0
    assert data.t90_min == 3.4
    assert data.spo2_moyenne == 93.6
    assert data.spo2_minimale == 85.0
    assert data.imc == 37.1
    assert data.temps_analyse_min == 352.4
    assert data.temps_enregistrement_min == 479.9
    assert data.activations_autonomiques == 51.5
    assert data.temps_eveil_min == 22.0
    assert data.ronflement_pct == 37.9
    assert data.ronflement_index == 347.5
    assert data.ronflement_dbc_moy == 72.3
    assert data.ronflement_dbc_max == 97.5
    assert data.fc_moyenne == 61.6
    assert data.fc_maximale == 93.0
    assert data.position_dorsale_pct == 9.9
    assert data.evenements_respiratoires["hypopnées"] == 68
    assert data.evenements_respiratoires["apnées centrales"] == 7


def test_contexte_clinique_d_indications(data):
    assert data.epworth == 6
    assert data.pichot == 18
    assert data.boss == 0
    ctx = default_context(data)
    assert ctx.type_examen == "controle_oam"
    assert "post OAM" in data.indications


def test_analyse_dossier_reel(data):
    res = analyse(data)
    assert res.severite == "légère"
    assert "OAM" in res.proposition_therapeutique or "IAH < 15" in res.proposition_therapeutique
    assert "positionnelle" in " ".join(res.interpretation).lower()
