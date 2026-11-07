"""Génération des documents : compte rendu, mémo, alertes, courrier (MD + DOCX)."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .analysis import AnalysisResult
from .models import PolygraphData

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
        return "non renseigné"
    return f"{v:g}{unit}" if unit else f"{v:g}"


def context(data: PolygraphData, res: AnalysisResult, medecin: str = "") -> dict:
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
        "imc": _fmt(data.imc),
        "epworth": _fmt(data.epworth),
        "duree": _fmt(data.temps_enregistrement_min),
        "analyse": _fmt(data.temps_analyse_min),
        "iah": _fmt(data.iah),
        "ia": _fmt(data.index_apnees),
        "ih": _fmt(data.index_hypopnees),
        "odi": _fmt(data.index_desat),
        "iah_dorsal": _fmt(data.iah_dorsal),
        "iah_lateral": _fmt(data.iah_latéral),
        "iah_rem": _fmt(data.iah_rem),
        "ronflement": _fmt(data.ronflement_pct),
        "dorsal": _fmt(data.position_dorsale_pct),
        "spo2_moy": _fmt(data.spo2_moyenne),
        "spo2_min": _fmt(data.spo2_minimale),
        "t90": _fmt(data.t90),
        "micro": _fmt(data.index_micro_eveils),
        "plm": _fmt(data.index_plm),
        "fc_moy": _fmt(data.fc_moyenne),
        "fc_max": _fmt(data.fc_maximale),
    }


def render(doc: str, data: PolygraphData, res: AnalysisResult, medecin: str = "") -> str:
    if doc not in DOCS:
        raise ValueError(f"Document inconnu : {doc}")
    return _env.get_template(f"{doc}.j2").render(**context(data, res, medecin))


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


def generate_all(data: PolygraphData, res: AnalysisResult, out_dir: str | Path, medecin: str = "") -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = (data.patient or "patient").split()[0].replace("/", "_") or "patient"
    outputs = {}
    for doc in DOCS:
        text = render(doc, data, res, medecin)
        md_path = out_dir / f"{base}_{doc}.md"
        md_path.write_text(text, encoding="utf-8")
        docx_path = out_dir / f"{base}_{doc}.docx"
        title = {
            "compte_rendu": "Compte rendu de polygraphie ventilatoire",
            "memo": "Mémo praticien",
            "alertes": "Points d'alerte",
            "courrier": "Courrier au médecin traitant",
        }[doc]
        _write_docx(text, docx_path, title)
        outputs[doc] = {"md": str(md_path), "docx": str(docx_path)}
    return outputs
