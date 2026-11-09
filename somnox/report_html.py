"""Rendu visuel (HTML MD3) du mémo praticien et des points d'alerte — pour l'interface."""

from __future__ import annotations

from .analysis import AnalysisResult
from .models import TYPE_EXAMEN_LABELS, ClinicalContext, PolygraphData

_SEV_STYLE = {
    "sévère": ("#B3261E", "#FFDAD6"),
    "modérée": ("#8D5000", "#FFE0B2"),
    "légère": ("#33691E", "#E8F3D8"),
    "absente": ("#1D1B20", "#E7E0EC"),
    "Non interprétable": ("#49454F", "#E7E0EC"),
}
_NIVEAUX = {
    "critique": ("#B3261E", "#FFDAD6", "&#9888;&#65039;"),
    "attention": ("#8D5000", "#FFE0B2", "&#9873;"),
    "info": ("#4F378B", "#EADDFF", "&#8505F0;"),
}


DOC_CSS = (
    "font-family:'Segoe UI',Roboto,sans-serif;font-size:14px;color:#1D1B20;line-height:1.6;"
)


def text_to_html(text: str) -> str:
    """Convertit le texte d'un document (compte rendu, courrier) en HTML stylé."""
    import html as _html
    import re

    out = [f"<div style='{DOC_CSS}'>"]
    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        esc = _html.escape(line)
        if re.match(r"^\d+\.\s+[A-ZÉÈÀ]", line):
            out.append(f"<h3 style='color:#6750A4;margin:14px 0 4px 0;'>{esc}</h3>")
        elif line.startswith("- "):
            out.append(f"<li style='margin:2px 0;'>{_html.escape(line[2:])}</li>")
        elif line.isupper() and len(line) > 3:
            out.append(f"<h2 style='color:#4F378B;margin:12px 0 4px 0;'>{_html.escape(line.title())}</h2>")
        else:
            out.append(f"<p style='margin:4px 0;'>{esc}</p>")
    out.append("</div>")
    return "".join(out)


def _chip(label: str, value: str, color: str = "#4F378B", bg: str = "#EADDFF") -> str:
    return (
        f"<span style='display:inline-block;background:{bg};color:{color};"
        f"border-radius:14px;padding:4px 12px;margin:2px;font-weight:600;'>"
        f"{label} <b>{value}</b></span>"
    )


def _severity_chip(severite: str) -> str:
    color, bg = _SEV_STYLE.get(severite, _SEV_STYLE["Non interprétable"])
    return (
        f"<span style='display:inline-block;background:{bg};color:{color};"
        f"border-radius:18px;padding:8px 18px;font-size:15px;font-weight:700;'>"
        f"{severite.upper()}</span>"
    )


def _section(title: str, color: str, body: str) -> str:
    return (
        f"<p style='color:{color};font-size:14px;font-weight:700;"
        f"margin:16px 0 4px 0;'>{title}</p>{body}"
    )


def _metric_chips(data: PolygraphData) -> str:
    def fmt(v, unit=""):
        return "—" if v is None else f"{v:g}{unit}"

    chips = [
        _chip("IAH", fmt(data.iah, "/h")),
        _chip("IDO", fmt(data.index_desat, "/h")),
        _chip("IAHo", fmt(data.iaho, "/h")),
        _chip("IAHc", fmt(data.iahc, "/h")),
        _chip("SpO2 min", fmt(data.spo2_minimale, " %"), "#B3261E" if (data.spo2_minimale or 100) < 90 else "#1D1B20", "#E7E0EC"),
        _chip("T90", fmt(data.t90, " %")),
        _chip("Charge hypox.", fmt(data.charge_hypoxique)),
        _chip("IAH dorsal", fmt(data.iah_dorsal, "/h"), "#8D5000" if (data.iah_dorsal or 0) >= 30 else "#4F378B", "#FFE0B2" if (data.iah_dorsal or 0) >= 30 else "#EADDFF"),
        _chip("AA", fmt(data.activations_autonomiques, "/h")),
        _chip("PLM", fmt(data.index_plm, "/h")),
    ]
    return "<div>" + "".join(chips) + "</div>"


def _alertes_html(alertes) -> str:
    if not alertes:
        return "<p style='color:#33691E;'>&#10003; Aucune alerte majeure détectée.</p>"
    out = []
    for a in alertes:
        color, bg, icon = _NIVEAUX.get(a.niveau, _NIVEAUX["info"])
        out.append(
            f"<div style='background:{bg};border-left:5px solid {color};"
            f"border-radius:12px;padding:8px 12px;margin:6px 0;'>"
            f"<span style='color:{color};font-weight:700;'>{icon} {a.titre}</span>"
            f"<br><span style='color:#1D1B20;'>{a.texte}</span></div>"
        )
    return "".join(out)


def _list_html(items) -> str:
    return "".join(f"<li style='margin:2px 0;'>{i}</li>" for i in items) or "<li>—</li>"


def memo_html(data: PolygraphData, res: AnalysisResult, ctx: ClinicalContext | None = None) -> str:
    ctx = ctx or ClinicalContext(epworth=data.epworth, pichot=data.pichot, boss=data.boss)
    vig_imm = [v["texte"] for v in res.vigilance if v["horizon"] == "immédiat"]
    vig_terme = [v["texte"] for v in res.vigilance if v["horizon"] == "à terme"]
    parts = [
        f"<h2 style='color:#6750A4;margin:0;'>Mémo praticien — {data.patient or 'Patient(e)'}</h2>",
        f"<p style='color:#49454F;margin:2px 0;'>{data.date_examen} &nbsp;·&nbsp; "
        f"{TYPE_EXAMEN_LABELS.get(ctx.type_examen, '')}</p>",
        _severity_chip(res.severite),
        _metric_chips(data),
        _section("PROPOSITION (remboursement)", "#4F378B",
                 f"<div style='background:#EADDFF;border-radius:12px;padding:8px 12px;'>"
                 f"<b>{res.proposition_therapeutique}</b></div>"),
        _section("CE QUE VOUS AURIEZ PU OUBLIER — IMMÉDIAT", "#B3261E",
                 f"<ul style='margin:4px 0;'>{_list_html(vig_imm)}</ul>"),
        _section("VIGILANCE À TERME", "#8D5000",
                 f"<ul style='margin:4px 0;'>{_list_html(vig_terme)}</ul>"),
        _section("&#9989; CHECKLIST AVANT VALIDATION", "#1D1B20",
                 "<div style='background:#FEF7FF;border:1px dashed #6750A4;border-radius:12px;"
                 "padding:8px 12px;'><ul style='margin:4px 0;'>"
                 + _list_html(res.checklist) + "</ul></div>"),
        _section("DIAGNOSTICS DIFFÉRENTIELS", "#4F378B",
                 f"<ul style='margin:4px 0;'>{_list_html(res.diagnostics_differentiels)}</ul>"),
        _section("BILAN COMPLÉMENTAIRE", "#4F378B",
                 f"<ul style='margin:4px 0;'>{_list_html(res.bilan_complementaire)}</ul>"),
        _section("ALERTES DU DOSSIER", "#B3261E", _alertes_html(res.alertes)),
        _section("INTERPRÉTATION (recommandations françaises)", "#4F378B",
                 f"<ul style='margin:4px 0;'>{_list_html(res.interpretation)}</ul>"),
        _section("FIABILITÉ", "#49454F", f"<p>{res.fiabilite}</p>"),
    ]
    if res.rappel_arrete:
        parts.append(_section("RAPPEL CONDUITE (arrêté 28/03/2022)", "#B3261E",
                              f"<p style='background:#FFDAD6;border-radius:12px;padding:8px 12px;'>{res.rappel_arrete}</p>"))
    return "".join(parts)


def alertes_html(data: PolygraphData, res: AnalysisResult, ctx: ClinicalContext | None = None) -> str:
    ctx = ctx or ClinicalContext(epworth=data.epworth, pichot=data.pichot, boss=data.boss)
    parts = [
        f"<h2 style='color:#6750A4;margin:0;'>Points d'alerte — {data.patient or 'Patient(e)'}</h2>",
        f"<p style='color:#49454F;margin:2px 0;'>{data.date_examen} · "
        f"IAH {'—' if data.iah is None else f'{data.iah:g}/h'}</p>",
        _severity_chip(res.severite),
        _alertes_html(res.alertes),
    ]
    vig_imm = [v["texte"] for v in res.vigilance if v["horizon"] == "immédiat"]
    if vig_imm:
        parts.append(_section("À CONTRÔLER AVANT VALIDATION", "#B3261E",
                              f"<ul style='margin:4px 0;'>{_list_html(vig_imm)}</ul>"))
    if res.donnees_manquantes:
        parts.append(_section("DONNÉES NON EXTRACTIBLES", "#8D5000",
                              f"<p>{', '.join(res.donnees_manquantes)}</p>"))
    return "".join(parts)
