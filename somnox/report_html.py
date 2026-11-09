"""Rendu visuel (HTML MD3 bleu) du mémo praticien et des points d'alerte — pour l'interface."""

from __future__ import annotations

from .analysis import AnalysisResult
from .models import TYPE_EXAMEN_LABELS, ClinicalContext, PolygraphData

PRIMARY = "#0B57D0"
PRIMARY_CONTAINER = "#D3E3FD"
ON_PRIMARY_CONTAINER = "#041E49"
SURFACE = "#F8F9FF"
OUTLINE = "#C4C7C5"

_SEV_STYLE = {
    "sévère": ("#FFFFFF", "#B3261E"),
    "modérée": ("#FFFFFF", "#E8590C"),
    "légère": ("#FFFFFF", "#2E6B1E"),
    "absente": ("#FFFFFF", "#49454F"),
    "Non interprétable": ("#FFFFFF", "#79747E"),
}
_NIVEAUX = {
    "critique": ("#B3261E", "#FCEBE9", "&#9888;&#65039;"),
    "attention": ("#8D5000", "#FCEFDF", "&#9873;"),
    "info": ("#0B57D0", "#D3E3FD", "&#8505F0;"),
}


def _fmt(v, unit=""):
    return "—" if v is None else f"{v:g}{unit}"


def _chip(label: str, value: str, ref: str = "", color: str = ON_PRIMARY_CONTAINER, bg: str = PRIMARY_CONTAINER) -> str:
    ref_html = f" <span style='font-weight:400;font-size:11px;color:{color};opacity:0.8;'>{ref}</span>" if ref else ""
    return (
        f"<span style='display:inline-block;background:{bg};color:{color};"
        f"border-radius:14px;padding:5px 13px;margin:3px;font-weight:700;font-size:13px;'>"
        f"{label} {value}{ref_html}</span>"
    )


def _severity_banner(severite: str, iah) -> str:
    fg, bg = _SEV_STYLE.get(severite, _SEV_STYLE["Non interprétable"])
    iah_txt = f"IAH {_fmt(iah, '/h')}" if iah is not None else ""
    return (
        f"<div style='background:{bg};color:{fg};border-radius:18px;padding:12px 20px;"
        f"font-size:17px;font-weight:800;margin:10px 0;'>"
        f"SÉVÉRITÉ : {severite.upper()} &nbsp;&nbsp;·&nbsp;&nbsp; {iah_txt}</div>"
    )


def _section(title: str, icon: str, body: str, color: str = PRIMARY) -> str:
    return (
        f"<div style='margin-top:18px;'><span style='font-size:15px;font-weight:800;"
        f"color:{color};'>{icon} {title}</span>{body}</div>"
    )


def _card(body: str, bg: str = SURFACE, border: str = OUTLINE) -> str:
    return f"<div style='background:{bg};border:1px solid {border};border-radius:14px;padding:10px 14px;margin:6px 0;'>{body}</div>"


def _score_chips(ctx: ClinicalContext, data: PolygraphData) -> str:
    ep = ctx.epworth if ctx.epworth is not None else data.epworth
    pi = ctx.pichot if ctx.pichot is not None else data.pichot
    bo = ctx.boss if ctx.boss is not None else data.boss
    chips = [
        _chip("Epworth", _fmt(ep), "/24"),
        _chip("Pichot", _fmt(pi), "/32"),
        _chip("BOSS", _fmt(bo), "/8"),
    ]
    return "<div>" + "".join(chips) + "</div>"


def _metric_group(title: str, pairs: list[tuple[str, str, str]]) -> str:
    chips = "".join(_chip(lbl, val, ref) for lbl, val, ref in pairs)
    return (
        f"<div style='margin-top:8px;'><span style='font-weight:700;color:{ON_PRIMARY_CONTAINER};"
        f"font-size:12px;text-transform:uppercase;letter-spacing:0.5px;'>{title}</span>"
        f"<div>{chips}</div></div>"
    )


def _metrics(data: PolygraphData) -> str:
    resp = [
        ("IAH", _fmt(data.iah, "/h"), ""),
        ("IAHo", _fmt(data.iaho, "/h"), "obstructif"),
        ("IAHc", _fmt(data.iahc, "/h"), "central"),
        ("IDO", _fmt(data.index_desat, "/h"), ""),
        ("Dorsal", _fmt(data.iah_dorsal, "/h"), "IAH"),
        ("Non-dorsal", _fmt(data.iah_latéral, "/h"), "IAH"),
        ("REM", _fmt(data.iah_rem, "/h"), "IAH"),
    ]
    oxy = [
        ("SpO2 moy", _fmt(data.spo2_moyenne, " %"), ""),
        ("SpO2 min", _fmt(data.spo2_minimale, " %"), ""),
        ("T90", _fmt(data.t90, " %"), f"{_fmt(data.t90_min, ' min')}"),
        ("Charge hypox.", _fmt(data.charge_hypoxique), "%min/h"),
    ]
    sommeil = [
        ("AA", _fmt(data.activations_autonomiques, "/h"), "activations autonomiques"),
        ("Éveil", _fmt(data.temps_eveil_min, " min"), ""),
        ("TTS", _fmt(data.temps_sommeil_estime_min, " min"), "sommeil est."),
        ("Qualité", _fmt(data.qualite_enregistrement_pct, " %"), "signal"),
        ("PLM", _fmt(data.index_plm, "/h"), ""),
    ]
    return (
        _metric_group("Respiratoire", resp)
        + _metric_group("Oxymétrie", oxy)
        + _metric_group("Sommeil / divers", sommeil)
    )


def _alertes_html(alertes) -> str:
    if not alertes:
        return "<p style='color:#2E6B1E;font-weight:600;'>&#10003; Aucune alerte majeure détectée.</p>"
    out = []
    for a in alertes:
        color, bg, icon = _NIVEAUX.get(a.niveau, _NIVEAUX["info"])
        out.append(
            f"<div style='background:{bg};border-left:5px solid {color};"
            f"border-radius:12px;padding:9px 13px;margin:7px 0;'>"
            f"<span style='color:{color};font-weight:800;'>{icon} ATTENTION — {a.titre}</span>"
            f"<br><span style='color:#1D1B20;'>{a.texte}</span></div>"
        )
    return "".join(out)


def _steps_html(items: list[str]) -> str:
    if not items:
        return "<p style='color:#2E6B1E;'>&#10003; Rien à signaler.</p>"
    rows = "".join(
        f"<div style='display:flex;align-items:flex-start;margin:7px 0;'>"
        f"<span style='min-width:22px;height:22px;border-radius:7px;background:{PRIMARY_CONTAINER};"
        f"color:{ON_PRIMARY_CONTAINER};font-weight:800;text-align:center;line-height:22px;"
        f"margin-right:10px;font-size:12px;'>{i + 1}</span>"
        f"<span style='flex:1;'>{t}</span></div>"
        for i, t in enumerate(items)
    )
    return f"<div style='margin:4px 0;'>{rows}</div>"


def _list_html(items) -> str:
    if not items:
        return "<p style='color:#2E6B1E;'>&#10003; Rien à signaler.</p>"
    return "".join(f"<li style='margin:3px 0;'>{i}</li>" for i in items)


def _suivi_oam_html(ctx: ClinicalContext) -> str:
    rows = []
    if ctx.observance_jours_sem is not None or ctx.observance_heures_nuit is not None:
        obs = "Observance : "
        if ctx.observance_jours_sem is not None:
            obs += f"<b>{ctx.observance_jours_sem} j/sem</b>"
        if ctx.observance_heures_nuit is not None:
            obs += f", <b>{ctx.observance_heures_nuit:g} h/nuit</b>"
        rows.append(obs)
    if ctx.tolerance_oam:
        rows.append(f"Tolérance : <b>{ctx.tolerance_oam}</b>")
    if ctx.reglage_oam_mm is not None:
        aug = f" (+{ctx.reglage_augmentation_mm:g} mm depuis la pose)" if ctx.reglage_augmentation_mm is not None else ""
        rows.append(f"Réglage actuel : <b>{ctx.reglage_oam_mm:g} mm</b>{aug}")
    if ctx.nycturie_fois is not None:
        rows.append(f"Nycturie : <b>{ctx.nycturie_fois} fois</b>")
    if ctx.efficacite_clinique:
        rows.append(f"Efficacité clinique : <b>{ctx.efficacite_clinique}</b>")
    if ctx.indication_controle_oam is not None:
        rows.append(f"Indication PGV de contrôle sous OAM : <b>{'Oui' if ctx.indication_controle_oam else 'Non (réglage à poursuivre)'}</b>")
    return _card("<div style='display:grid;'>" + "<br>".join(rows) + "</div>")


def memo_html(data: PolygraphData, res: AnalysisResult, ctx: ClinicalContext | None = None) -> str:
    ctx = ctx or ClinicalContext(epworth=data.epworth, pichot=data.pichot, boss=data.boss)
    vig_imm = [v["texte"] for v in res.vigilance if v["horizon"] == "immédiat"]
    vig_terme = [v["texte"] for v in res.vigilance if v["horizon"] == "à terme"]

    parts = [
        f"<h2 style='color:{PRIMARY};margin:0;font-size:20px;'>&#129503; Mémo praticien — {data.patient or 'Patient(e)'}</h2>",
        f"<p style='color:#49454F;margin:4px 0;'>{data.date_examen} &nbsp;·&nbsp; "
        f"<b>{TYPE_EXAMEN_LABELS.get(ctx.type_examen, '')}</b> &nbsp;·&nbsp; {res.fiabilite}</p>",
        _severity_banner(res.severite, data.iah),
        _section("Scores cliniques", "&#128202;", _score_chips(ctx, data)),
        *([] if ctx.type_examen != "controle_oam" or ctx.observance_heures_nuit is None and not ctx.tolerance_oam and ctx.reglage_oam_mm is None and not ctx.efficacite_clinique
           else [_section("Suivi OAM (4 mois)", "&#128367;&#65039;", _suivi_oam_html(ctx))]),
        _section("Métriques", "&#128200;", _metrics(data)),
        _section("Checklist avant validation — étape par étape", "&#9989;", _steps_html(res.checklist)),
        _section("Vigilance immédiate", "&#9888;&#65039;", _card(_list_html(vig_imm), "#FCEBE9", "#F3B8B2"),
                 "#B3261E"),
        _section("Vigilance à terme", "&#128197;", _card(_list_html(vig_terme), "#FCEFDF", "#EFC49A"),
                 "#8D5000"),
        _section("Proposition thérapeutique (remboursement)", "&#128138;",
                 _card(f"<b>{res.proposition_therapeutique}</b>")),
        _section("Diagnostics différentiels", "&#128269;", _card(_list_html(res.diagnostics_differentiels))),
        _section("Bilan complémentaire", "&#129514;", _card(_list_html(res.bilan_complementaire))),
        _section("Alertes du dossier", "&#128680;", _alertes_html(res.alertes), "#B3261E"),
        _section("Interprétation (recommandations françaises)", "&#128218;",
                 f"<ul style='margin:4px 0;'>{_list_html(res.interpretation)}</ul>"),
    ]
    if res.rappel_arrete:
        parts.append(_section("Conduite automobile (arrêté du 28/03/2022)", "&#128663;",
                              _card(res.rappel_arrete, "#FCEBE9", "#F3B8B2"), "#B3261E"))
    return "".join(parts)


def alertes_html(data: PolygraphData, res: AnalysisResult, ctx: ClinicalContext | None = None) -> str:
    ctx = ctx or ClinicalContext(epworth=data.epworth, pichot=data.pichot, boss=data.boss)
    parts = [
        f"<h2 style='color:{PRIMARY};margin:0;font-size:20px;'>&#128680; Points d'alerte — {data.patient or 'Patient(e)'}</h2>",
        f"<p style='color:#49454F;margin:4px 0;'>{data.date_examen} · "
        f"IAH {_fmt(data.iah, '/h')}</p>",
        _severity_banner(res.severite, data.iah),
        _alertes_html(res.alertes),
    ]
    vig_imm = [v["texte"] for v in res.vigilance if v["horizon"] == "immédiat"]
    if vig_imm:
        parts.append(_section("À contrôler avant validation", "&#9888;&#65039;",
                              _card(_list_html(vig_imm), "#FCEBE9", "#F3B8B2"), "#B3261E"))
    if res.donnees_manquantes:
        parts.append(_section("Données non extractibles", "&#9878;&#65039;",
                              _card(", ".join(res.donnees_manquantes), "#FCEFDF", "#EFC49A"), "#8D5000"))
    return "".join(parts)


DOC_CSS = (
    "font-family:'Segoe UI',Roboto,sans-serif;font-size:14px;color:#1D1B20;line-height:1.65;"
)


def text_to_html(text: str) -> str:
    """Convertit le texte d'un document (compte rendu, courrier) en HTML structuré."""
    import html as _html
    import re

    out = [f"<div style='{DOC_CSS}'>"]
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            close_list()
            out.append("<div style='height:8px;'></div>")
            continue
        esc = _html.escape(line)
        if re.match(r"^\d+\.\s+[A-ZÉÈÀ]", line):
            close_list()
            out.append(f"<h3 style='color:{PRIMARY};margin:16px 0 6px 0;font-size:15px;'>{esc}</h3>")
        elif line.startswith("- "):
            if not in_list:
                out.append("<ul style='margin:4px 0 4px 18px;padding:0;'>")
                in_list = True
            content = _html.escape(line[2:])
            if ":" in content:
                label, _, rest = content.partition(":")
                content = f"<b>{label}</b> :{rest}"
            out.append(f"<li style='margin:5px 0;'>{content}</li>")
        elif line.isupper() and len(line) > 3:
            close_list()
            out.append(f"<h2 style='color:{ON_PRIMARY_CONTAINER};margin:14px 0 6px 0;'>{_html.escape(line.title())}</h2>")
        else:
            close_list()
            content = esc
            if ":" in line and len(line.split(":", 1)[0]) < 40:
                label, _, rest = esc.partition(":")
                content = f"<b>{label}</b> :{rest}"
            out.append(f"<p style='margin:5px 0;'>{content}</p>")
    close_list()
    out.append("</div>")
    return "".join(out)
