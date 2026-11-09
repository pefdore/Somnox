"""Pipeline complet : PDF -> texte -> parsing -> analyse -> documents."""

from __future__ import annotations

from pathlib import Path

from .analysis import AnalysisResult, analyse
from .generate import generate_all
from .models import ClinicalContext, PolygraphData, default_context
from .parser import parse_pdf


def process_pdf(
    pdf_path: str | Path,
    out_dir: str | Path,
    ctx: ClinicalContext | None = None,
    medecin: str = "",
) -> tuple[PolygraphData, AnalysisResult, dict]:
    data = parse_pdf(pdf_path)
    res = analyse(data, ctx or default_context(data))
    outputs = generate_all(data, res, out_dir, ctx, medecin)
    return data, res, outputs
