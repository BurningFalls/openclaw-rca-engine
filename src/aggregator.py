"""
Trend aggregator and report generator for RCA classification results.

Groups ClassificationResult objects by category, computes frequency and
confidence statistics, and outputs a ranked Markdown trend report.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from classifier import ClassificationResult

__all__ = ["TrendReport", "aggregate", "write_report"]

OUTPUT_DIR = Path(__file__).parent.parent / "output"

CATEGORY_LABELS = {
    "STALE": "Stale / No Contributor Response",
    "MERGE_CONFLICT": "Merge Conflicts",
    "CI_FAILURE": "CI/CD Failures",
    "ARCHITECTURAL_MISMATCH": "Architectural Mismatch",
    "SUPERSEDED": "Superseded by Other PR",
    "UNKNOWN": "Unknown",
}


@dataclass
class CategorySummary:
    category: str
    label: str
    count: int
    percentage: float
    avg_confidence: float
    examples: list[ClassificationResult]


@dataclass
class TrendReport:
    total_prs: int
    generated_at: str
    categories: list[CategorySummary]  # sorted by count descending
    low_confidence_prs: list[ClassificationResult]  # confidence < 0.5


def aggregate(results: list[ClassificationResult]) -> TrendReport:
    """
    Group classification results by category and compute summary statistics.

    Args:
        results: List of ClassificationResult from the classifier.

    Returns:
        TrendReport with ranked categories and flagged low-confidence PRs.
    """
    total = len(results)
    if total == 0:
        return TrendReport(
            total_prs=0,
            generated_at=datetime.now(timezone.utc).isoformat(),
            categories=[],
            low_confidence_prs=[],
        )

    buckets: dict[str, list[ClassificationResult]] = defaultdict(list)
    for r in results:
        buckets[r.category].append(r)

    summaries = []
    for category, items in buckets.items():
        avg_conf = sum(r.confidence for r in items) / len(items)
        # Up to 3 highest-confidence examples per category
        examples = sorted(items, key=lambda x: x.confidence, reverse=True)[:3]
        summaries.append(
            CategorySummary(
                category=category,
                label=CATEGORY_LABELS.get(category, category),
                count=len(items),
                percentage=len(items) / total * 100,
                avg_confidence=avg_conf,
                examples=examples,
            )
        )

    summaries.sort(key=lambda s: s.count, reverse=True)

    low_confidence = sorted(
        [r for r in results if r.confidence < 0.5],
        key=lambda r: r.confidence,
    )

    return TrendReport(
        total_prs=total,
        generated_at=datetime.now(timezone.utc).isoformat(),
        categories=summaries,
        low_confidence_prs=low_confidence,
    )


def _render_report(report: TrendReport) -> str:
    lines = [
        "# OpenClaw RCA — Failure Trend Report",
        "",
        f"**Generated:** {report.generated_at}  ",
        f"**Total PRs analyzed:** {report.total_prs}",
        "",
        "---",
        "",
        "## Failure Category Rankings",
        "",
        "| Rank | Category | Count | Share | Avg Confidence |",
        "|------|----------|-------|-------|----------------|",
    ]

    for i, s in enumerate(report.categories, 1):
        lines.append(
            f"| {i} | {s.label} | {s.count} | {s.percentage:.1f}% | {s.avg_confidence:.2f} |"
        )

    lines += ["", "---", ""]

    for s in report.categories:
        lines += [
            f"## {s.label} ({s.count} PR{'s' if s.count != 1 else ''})",
            "",
            f"**Share:** {s.percentage:.1f}%  ",
            f"**Average confidence:** {s.avg_confidence:.2f}",
            "",
            "### Top Examples",
            "",
        ]
        for r in s.examples:
            lines += [
                f"**PR #{r.pr_number} — {r.pr_title}**  ",
                f"Confidence: {r.confidence:.2f}  ",
                f"Reasoning: {r.reasoning}  ",
            ]
            if r.evidence:
                lines.append("Evidence:")
                for e in r.evidence:
                    lines.append(f"- {e}")
            lines.append("")

    if report.low_confidence_prs:
        lines += [
            "---",
            "",
            "## Low-Confidence Results (< 0.5) — Flagged for Human Review",
            "",
        ]
        for r in report.low_confidence_prs:
            lines += [
                f"- **PR #{r.pr_number}** ({r.category}, confidence={r.confidence:.2f}): {r.pr_title}",
            ]
        lines.append("")

    return "\n".join(lines)


def write_report(report: TrendReport, path: Path | None = None) -> Path:
    """
    Write the trend report to a Markdown file.

    Args:
        report: TrendReport from aggregate().
        path: Output file path. Defaults to output/report.md.

    Returns:
        Path of the written file.
    """
    if path is None:
        OUTPUT_DIR.mkdir(exist_ok=True)
        path = OUTPUT_DIR / "report.md"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render_report(report), encoding="utf-8")
    print(f"[aggregator] Report written to {path}")
    return path


