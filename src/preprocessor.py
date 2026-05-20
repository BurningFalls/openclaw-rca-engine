"""
Preprocessor for raw PRData: truncates diffs, formats comment threads,
and extracts CI failure signals before LLM classification.
"""

from dataclasses import dataclass

from github_client import PRData, ReviewData, CheckRunResult

__all__ = ["PreprocessedPR", "preprocess_pr", "preprocess_prs"]

_MAX_DIFF_CHARS = 3000
_MAX_COMMENT_CHARS = 2000
_MAX_BODY_CHARS = 500
_REVIEW_BODY_PREVIEW = 200
_CHECK_SUMMARY_PREVIEW = 200


@dataclass
class PreprocessedPR:
    number: int
    title: str
    author: str
    created_at: str
    closed_at: str | None
    labels: list[str]
    body_truncated: str
    check_runs_formatted: str
    reviews_formatted: str
    issue_comments_formatted: str
    review_comments_formatted: str
    diff_truncated: str
    failed_ci_count: int
    total_ci_count: int
    review_count: int
    issue_comment_count: int
    review_comment_count: int


def _format_reviews(reviews: list[ReviewData]) -> str:
    if not reviews:
        return "None"
    lines = []
    for r in reviews:
        body_preview = r.body[:_REVIEW_BODY_PREVIEW].strip() if r.body else ""
        lines.append(f"- [{r.state}] {r.author}: {body_preview}")
    return "\n".join(lines)


def _format_check_runs(check_runs: list[CheckRunResult]) -> str:
    if not check_runs:
        return "None"
    lines = []
    for c in check_runs:
        summary = c.output_summary[:_CHECK_SUMMARY_PREVIEW].strip() if c.output_summary else ""
        lines.append(
            f"- {c.name}: {c.conclusion or c.status}"
            + (f" — {c.output_title}" if c.output_title else "")
            + (f"\n  {summary}" if summary else "")
        )
    return "\n".join(lines)


def _format_comments(comments: list[str]) -> str:
    if not comments:
        return "None"
    joined = "\n---\n".join(comments)
    if len(joined) > _MAX_COMMENT_CHARS:
        return joined[:_MAX_COMMENT_CHARS] + "\n... [truncated]"
    return joined


def preprocess_pr(pr: PRData) -> PreprocessedPR:
    """
    Transform a raw PRData into a PreprocessedPR ready for LLM input.

    Truncates diffs and comments, extracts CI failure counts, and
    formats all fields into plain-text strings.
    """
    failed_ci = [c for c in pr.check_runs if c.conclusion in ("failure", "error")]

    return PreprocessedPR(
        number=pr.number,
        title=pr.title,
        author=pr.author,
        created_at=pr.created_at,
        closed_at=pr.closed_at,
        labels=list(pr.labels),
        body_truncated=pr.body[:_MAX_BODY_CHARS].strip() if pr.body else "No description provided.",
        check_runs_formatted=_format_check_runs(pr.check_runs),
        reviews_formatted=_format_reviews(pr.reviews),
        issue_comments_formatted=_format_comments(pr.issue_comments),
        review_comments_formatted=_format_comments(pr.review_comments),
        diff_truncated=pr.diff[:_MAX_DIFF_CHARS].strip() if pr.diff else "No diff available.",
        failed_ci_count=len(failed_ci),
        total_ci_count=len(pr.check_runs),
        review_count=len(pr.reviews),
        issue_comment_count=len(pr.issue_comments),
        review_comment_count=len(pr.review_comments),
    )


def preprocess_prs(prs: list[PRData]) -> list[PreprocessedPR]:
    """Preprocess a list of PRData objects in order."""
    print(f"[preprocessor] Preprocessing {len(prs)} PRs...")
    preprocessed = [preprocess_pr(pr) for pr in prs]
    print("[preprocessor] Done.")
    return preprocessed
