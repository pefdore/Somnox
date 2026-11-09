"""Format « Suivi OAM (4 mois) » dans les Indications."""

from somnox.analysis import analyse
from somnox.context import build_context
from somnox.models import PolygraphData
from somnox.parser import parse_text

SUIVI = """Rapport de polygraphie ventilatoire
Indications
Suivi OAM (4 mois) : Observance : 6 j/sem, 6 h/nuit | Tolérance : douleurs ATM | Réglage actuel : 7 mm (+2 mm depuis la pose)
Clinique : Somnolence diurne : non | Ronflements sévères : doute | Céphalées matinales : non | Fatigue diurne : parfois | Nycturie : 1 fois | Sensation d'étouffement : non
Scores : Pre-OAM -> Post-OAM : Epworth : 14 -> 6/24 | Pichot : 19 -> 8/32 | Boss : 4 -> 1/8
Métrique Initiale : IAH : 19,4/h | IDO : 18,4/h | T90 : 8% | CH : 20%min/h
Décision : Efficacité clinique complète -> Indication PGV de contrôle sous OAM : Oui
Paramètres respiratoires
Index Apnées Hypopnées
12 /h
"""


def _data():
    return parse_text(SUIVI, source="suivi.txt")


def test_parsing_suivi_oam():
    d = _data()
    ctx = build_context(d)
    assert ctx.type_examen == "controle_oam"
    assert ctx.observance_jours_sem == 6
    assert ctx.observance_heures_nuit == 6.0
    assert "ATM" in ctx.tolerance_oam
    assert ctx.reglage_oam_mm == 7.0
    assert ctx.reglage_augmentation_mm == 2.0
    assert ctx.ronflements_doute is True and ctx.ronflements_constates is False
    assert ctx.fatigue_parfois is True and ctx.fatigue is False
    assert ctx.nycturie_fois == 1 and ctx.nycturie is True
    assert ctx.epworth_pre == 14 and ctx.epworth == 6
    assert ctx.pichot_pre == 19 and ctx.pichot == 8
    assert ctx.boss_pre == 4 and ctx.boss == 1
    assert d.iah_pre_traitement == 19.4
    assert d.odi_pre_traitement == 18.4
    assert d.t90_pre_traitement == 8.0
    assert d.charge_hypoxique_pre_traitement == 20.0
    assert ctx.efficacite_clinique == "complète"
    assert ctx.indication_controle_oam is True


def test_regles_suivi_oam():
    d = _data()
    ctx = build_context(d)
    r = analyse(d, ctx)
    titres = [a.titre for a in r.alertes]
    assert "Intolérance OAM" in titres
    assert any("Epworth 14 → 6/24" in i for i in r.interpretation)
    assert any("T90 8 → " in i for i in r.interpretation)


def test_observance_insuffisante():
    d = parse_text(SUIVI.replace("6 h/nuit", "3 h/nuit").replace("12 /h", "10 /h"))
    ctx = build_context(d)
    r = analyse(d, ctx)
    assert any("Observance OAM insuffisante" in v["texte"] for v in r.vigilance)


def test_discordance_efficacite_nulle():
    d = parse_text(SUIVI.replace("Efficacité clinique complète", "Efficacité clinique nulle"))
    ctx = build_context(d)
    r = analyse(d, ctx)
    assert any("Discordance" in v["texte"] for v in r.vigilance)


def test_avance_mandibulaire_si_echec():
    d = parse_text(SUIVI.replace("12 /h", "20 /h").replace("(+2 mm depuis la pose)", "(+0.5 mm depuis la pose)"))
    ctx = build_context(d)
    r = analyse(d, ctx)
    assert any("avancée mandibulaire supplémentaire" in rec for rec in r.recommandations)


def test_memo_affiche_suivi_oam():
    from somnox.generate import render
    from somnox.report_html import memo_html

    d = _data()
    ctx = build_context(d)
    r = analyse(d, ctx)
    memo = render("memo", d, r, ctx)
    assert "SUIVI OAM (4 MOIS)" in memo
    assert "6 j/sem" in memo
    h = memo_html(d, r, ctx)
    assert "Suivi OAM (4 mois)" in h
    assert "douleurs ATM" in h


def test_critere_efficacite_oam_satisfaisante():
    # IAH 19,4 -> 12 : réduction 38 % -> critère NON rempli ; 19,4 -> 9 : 54 %, < 10 -> complète
    d = _data()
    ctx = build_context(d)
    r = analyse(d, ctx)
    assert any("non rempli" in i for i in r.interpretation)
    d2 = parse_text(SUIVI.replace("Index Apnées Hypopnées\n12 /h", "Index Apnées Hypopnées\n9 /h"))
    r2 = analyse(d2, build_context(d2))
    assert any("efficacité complète" in i for i in r2.interpretation)
    d3 = parse_text(SUIVI.replace("Index Apnées Hypopnées\n12 /h", "Index Apnées Hypopnées\n12 /h").replace("Métrique Initiale : IAH : 19,4/h", "Métrique Initiale : IAH : 30/h"))
    r3 = analyse(d3, build_context(d3))
    assert any("satisfaisante" in i for i in r3.interpretation)


def test_soh_obesite_severe_seule():
    from somnox.models import PolygraphData as PD

    d = PD(iah=20.0, temps_analyse_min=420, spo2_minimale=90, index_desat=20, imc=38, t90=1.0)
    r = analyse(d)
    assert any("SOH" in a.titre for a in r.alertes)


def test_soh_critique():
    from somnox.models import PolygraphData as PD

    d = PD(iah=25.0, temps_analyse_min=420, spo2_minimale=80, index_desat=25, imc=40, t90=12.0, spo2_moyenne=89)
    r = analyse(d)
    soh = [a for a in r.alertes if "SOH" in a.titre]
    assert soh and soh[0].niveau == "critique"
