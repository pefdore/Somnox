"""Tests du moteur expert : règles avancées (CSA, SOH, REM, discordance, OAM, bradycardie)."""

from somnox.analysis import analyse
from somnox.models import ClinicalContext, PolygraphData


def _data(**kw):
    base = dict(iah=20.0, temps_analyse_min=420, spo2_minimale=90, index_desat=20, temps_enregistrement_min=480)
    base.update(kw)
    return PolygraphData(**base)


def _titres(r):
    return [a.titre for a in r.alertes]


def test_predominance_centrale():
    d = _data(iaho=3.0, iahc=17.0)
    r = analyse(d)
    assert "Prédominance d'apnées centrales" in _titres(r)
    assert any("cardiologique" in b.lower() for b in r.bilan_complementaire)


def test_cheyne_stokes():
    d = _data(cheyne_stokes_min=25)
    r = analyse(d)
    assert "Respiration de Cheyne-Stokes" in _titres(r)
    assert any("Cheyne-Stokes" in b for b in r.bilan_complementaire)


def test_suspicion_soh():
    d = _data(imc=38, t90=8.0, spo2_moyenne=91)
    r = analyse(d)
    assert "Suspicion de syndrome d'obésité-hypoventilation (SOH)" in _titres(r)
    assert any("gaz du sang" in b.lower() for b in r.bilan_complementaire)


def test_sahos_rem():
    d = _data(iah=8.0, iah_rem=22.0, index_desat=8)
    r = analyse(d)
    assert any("REM" in i for i in r.interpretation)


def test_discordance_iah_ido():
    d = _data(iah=30.0, index_desat=5.0)
    r = analyse(d)
    assert any("Discordance IAH/IDO" in i for i in r.interpretation)
    assert any("Discordance" in v["texte"] for v in r.vigilance)


def test_qualite_faible():
    d = _data(qualite_enregistrement_pct=40)
    r = analyse(d)
    assert "faible" in r.fiabilite
    assert any("Qualité" in v["texte"] for v in r.vigilance)


def test_bradycardie():
    d = _data(fc_minimale=35)
    r = analyse(d)
    assert "Bradycardie nocturne" in _titres(r)


def test_checklist_oam():
    d = _data(iah=20.0)
    r = analyse(d, ClinicalContext())
    assert any("contre-indication dentaire" in c for c in r.checklist)


def test_somnolence_severe_differentiels():
    d = _data(iah=5.0, index_desat=5)
    r = analyse(d, ClinicalContext(somnolence=True, epworth=17))
    assert any("narcolepsie" in x.lower() for x in r.diagnostics_differentiels)
    assert any("TSH" in b for b in r.bilan_complementaire)


def test_shvas_suspicion():
    d = _data(iah=3.0, index_desat=3)
    r = analyse(d, ClinicalContext(somnolence=True, epworth=12))
    assert any("SHVAS" in x for x in r.diagnostics_differentiels)


def test_checklist_boss_manquant():
    d = _data(iah=20.0)
    r = analyse(d)
    assert any("BOSS" in c for c in r.checklist)


def test_observance_dans_suivi_ppc():
    d = _data(iah=35.0)
    r = analyse(d, ClinicalContext(comorbidites=["HTA"]))
    assert any("observance" in s.lower() for s in r.suivi)


def test_charge_hypoxique_elevee():
    d = _data(charge_hypoxique=75.0)
    r = analyse(d)
    assert "Charge hypoxique élevée" in _titres(r)


def test_charge_hypoxique_notable():
    d = _data(charge_hypoxique=25.0)
    r = analyse(d)
    assert any("Charge hypoxique" in i for i in r.interpretation)


def test_cycles_respiration_limitee_shvas():
    from somnox.models import ClinicalContext

    d = _data(iah=6.0, index_desat=6, cycles_respiration_limitee_pct=15.0)
    r = analyse(d, ClinicalContext(somnolence=True, epworth=13))
    assert any("respiration limitée" in i for i in r.interpretation)
    assert any("SHVAS" in x for x in r.diagnostics_differentiels)
