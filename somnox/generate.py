"""Génération des documents : conclusion, mémo vigilance, alertes, courrier (MD + DOCX)."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .analysis import AnalysisResult
from .models import ClinicalContext, PolygraphData, default_context

TEMPLATES_DIR = Path(__file__).parent / "templates"

DOCS = ("compte_rendu", "memo", "alertes", "courrier")

_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _fmt(v, unit=""):
    if v is None:
        return unit or "non renseigné"
    return f"{v:g}{unit}" if unit else f"{v:g}"


def _predominance(data: PolygraphData) -> str:
    o, c = data.iaho, data.iahc
    if o is None and c is None:
        obstructives = data.evenements_respiratoires.get("apnées obstructives", 0)
        tot_apnees = obstructives + data.evenements_respiratoires.get("apnées centrales", 0)
        if tot_apnees:
            o, c = obstructives, data.evenements_respiratoires.get("apnées centrales", 0)
    if o is not None and c is not None:
        if c > o:
            return "centrale"
        return "obstructive"
    return "non déterminée (événements obstructifs présumés)"


def _dependance_positionnelle(data: PolygraphData) -> str:
    d, nd = data.iah_dorsal, data.iah_latéral
    if d is None or nd is None:
        return "Analyse positionnelle non disponible."
    if nd > 0 and d / nd >= 2:
        return f"Dépendance positionnelle nette (IAH dorsal {d:g}/h vs non-dorsal {nd:g}/h)."
    return f"Pas de dépendance positionnelle franche (IAH dorsal {d:g}/h vs non-dorsal {nd:g}/h)."


def _grade_hypoxemie(data: PolygraphData) -> str:
    if data.spo2_moyenne is None and data.t90 is None:
        return "non évaluée"
    if (data.spo2_minimale or 100) < 80 or (data.t90 or 0) >= 15:
        return "sévère"
    if (data.spo2_minimale or 100) < 90 or (data.t90 or 0) >= 5:
        return "modérée"
    return "légère"


def _intensite_ronflement(data: PolygraphData) -> str:
    pct = data.ronflement_pct
    if pct is None:
        return "non quantifiés"
    if pct >= 40:
        return "extrêmes"
    if pct >= 20:
        return "modérés"
    return "légers"


def _symptomes(ctx: ClinicalContext, data: PolygraphData) -> str:
    items = []
    if ctx.somnolence or data.epworth is not None:
        ep = ctx.epworth if ctx.epworth is not None else data.epworth
        items.append(f"somnolence diurne (Epworth {ep}/24)")
    if ctx.fatigue or ctx.pichot is not None or data.pichot is not None:
        pichot = ctx.pichot if ctx.pichot is not None else data.pichot
        items.append(f"fatigue (Pichot {pichot if pichot is not None else 'non renseigné'})")
    if ctx.nycturie:
        items.append("nycturie")
    if ctx.cephees_matinales:
        items.append("céphalées matinales")
    if ctx.ronflements_constates:
        items.append("ronflements constatés par l'entourage")
    return ", ".join(items) if items else "pas de symptôme évocateur rapporté (à compléter si besoin)"


def _particularites(data: PolygraphData) -> str:
    lines = []
    if data.iah_rem is not None:
        lines.append(f"- Aggravation en REM (IAH {data.iah_rem:g}/h, SpO2 min {data.spo2_min_rem if data.spo2_min_rem is not None else data.spo2_minimale} %).")
    if data.activations_autonomiques is not None:
        lines.append(f"- Activations autonomiques à {data.activations_autonomiques:g}/h.")
    if data.temps_eveil_min is not None:
        lines.append(f"- Fragmentation du sommeil ({data.temps_eveil_min:g} min d'éveil).")
    if data.index_plm is not None and data.index_plm >= 15:
        lines.append(f"- Mouvements périodiques des jambes (index {data.index_plm:g}/h).")
    return "\n".join(lines) if lines else "- Rien de particulier à signaler."


def context(data: PolygraphData, res: AnalysisResult, ctx: ClinicalContext | None = None, medecin: str = "") -> dict:
    ctx = ctx or default_context(data)
    return {
        "patient": data.patient or "Patient(e)",
        "date_examen": data.date_examen or "date non retrouvée",
        "severite": res.severite,
        "conclusion": res.conclusion,
        "fiabilite": res.fiabilite,
        "interpretation": res.interpretation,
        "alertes": [vars(a) for a in res.alertes],
        "recommandations": res.recommandations,
        "donnees_manquantes": res.donnees_manquantes,
        "medecin": medecin,
        "iah": _fmt(data.iah),
        "iaho": _fmt(data.iaho, "—") if data.iaho is None else _fmt(data.iaho),
        "iahc": _fmt(data.iahc, "—") if data.iahc is None else _fmt(data.iahc),
        "iah_dorsal": _fmt(data.iah_dorsal),
        "iah_lateral": _fmt(data.iah_latéral),
        "iah_rem": _fmt(data.iah_rem),
        "predominance": _predominance(data),
        "dependance_positionnelle": _dependance_positionnelle(data),
        "grade_hypoxemie": _grade_hypoxemie(data),
        "intensite_ronflement": _intensite_ronflement(data),
        "symptomes": _symptomes(ctx, data),
        "particularites": _particularites(data),
        "proposition": res.proposition_therapeutique,
        "mesures": res.mesures_associees,
        "suivi": res.suivi,
        "rappel_arrete": res.rappel_arrete,
        "vigilance_immédiat": [v["texte"] for v in res.vigilance if v["horizon"] == "immédiat"],
        "vigilance_terme": [v["texte"] for v in res.vigilance if v["horizon"] == "à terme"],
        "odi": _fmt(data.index_desat),
        "ia": _fmt(data.index_apnees),
        "ih": _fmt(data.index_hypopnees),
        "spo2_moy": _fmt(data.spo2_moyenne),
        "spo2_min": _fmt(data.spo2_minimale),
        "t90": _fmt(data.t90),
        "t90_min": _fmt(data.t90_min, "—") if data.t90_min is None else _fmt(data.t90_min),
        "charge_hypoxique": _fmt(data.charge_hypoxique, "—") if data.charge_hypoxique is None else _fmt(data.charge_hypoxique),
        "ronflement": _fmt(data.ronflement_pct),
        "dbc_moy": _fmt(data.ronflement_dbc_moy, "—") if data.ronflement_dbc_moy is None else _fmt(data.ronflement_dbc_moy),
        "dbc_max": _fmt(data.ronflement_dbc_max, "—") if data.ronflement_dbc_max is None else _fmt(data.ronflement_dbc_max),
        "micro": _fmt(data.index_micro_eveils),
        "plm": _fmt(data.index_plm),
        "fc_moy": _fmt(data.fc_moyenne),
        "fc_max": _fmt(data.fc_maximale),
        "imc": _fmt(data.imc),
        "duree": _fmt(data.temps_enregistrement_min),
        "analyse": _fmt(data.temps_analyse_min),
    }


def render(doc: str, data: PolygraphData, res: AnalysisResult, ctx: ClinicalContext | None = None, medecin: str = "") -> str:
    if doc not in DOCS:
        raise ValueError(f"Document inconnu : {doc}")
    return _env.get_template(f"{doc}.j2").render(**context(data, res, ctx, medecin))


def _write_docx(text: str, path: Path, title: str) -> None:
    d = Document()
    d.add_heading(title, 0)
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if line.isupper() and len(line) > 3:
            d.add_heading(line.title(), level=2)
        else:
            d.add_paragraph(line)
    d.save(path)


def generate_all(data: PolygraphData, res: AnalysisResult, out_dir: str | Path, ctx: ClinicalContext | None = None, medecin: str = "") -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = (data.patient or "patient").split()[0].replace("/", "_") or "patient"
    outputs = {}
    for doc in DOCS:
        text = render(doc, data, res, ctx, medecin)
        md_path = out_dir / f"{base}_{doc}.md"
        md_path.write_text(text, encoding="utf-8")
        docx_path = out_dir / f"{base}_{doc}.docx"
        title = {
            "compte_rendu": "Conclusion de polygraphie ventilatoire",
            "memo": "Mémo praticien — points de vigilance",
            "alertes": "Points d'alerte",
            "courrier": "Courrier au médecin traitant",
        }[doc]
        _write_docx(text, docx_path, title)
        outputs[doc] = {"md": str(md_path), "docx": str(docx_path)}
    return outputs
