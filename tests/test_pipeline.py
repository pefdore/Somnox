from pathlib import Path

from somnox.analysis import analyse
from somnox.generate import generate_all, render
from somnox.parser import parse_text

SAMPLE = Path(__file__).parent / "samples" / "noxt3s_sample.txt"


def _data():
    return parse_text(SAMPLE.read_text(encoding="utf-8"), source="sample.txt", methode="test")


def test_parse_metrics():
    d = _data()
    assert d.patient == "DUPONT Jean"
    assert d.iah == 47.3
    assert d.index_apnees == 18.5
    assert d.index_desat == 43.1
    assert d.spo2_minimale == 74
    assert d.t90 == 18.6
    assert d.imc == 30.4
    assert d.epworth == 14
    assert d.temps_analyse_min == 432


def test_analysis_severe():
    r = analyse(_data())
    assert r.severite == "sévère"
    assert any(a.niveau == "critique" for a in r.alertes)
    assert r.fiabilite.startswith("Enregistrement de durée")


def test_analysis_inconclusive():
    from somnox.models import PolygraphData

    r = analyse(PolygraphData(temps_analyse_min=120, iah=3.0))
    assert "non concluant" in r.fiabilite


def test_render_and_generate(tmp_path):
    d = _data()
    r = analyse(d)
    for doc in ("compte_rendu", "memo", "alertes", "courrier"):
        text = render(doc, d, r)
        assert "IAH" in text or "Alerte" in text or doc == "courrier"
    outputs = generate_all(d, r, tmp_path)
    assert all(Path(p["docx"]).exists() for p in outputs.values())
    assert all(Path(p["md"]).exists() for p in outputs.values())


def test_positional_component():
    d = _data()
    r = analyse(d)
    assert any("positionnelle" in i for i in r.interpretation)
