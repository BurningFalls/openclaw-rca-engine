"""
LLM-based root cause analysis classifier for abandoned pull requests.

Uses the Claude API with prompt caching to classify each PR into one of five
failure categories: STALE, MERGE_CONFLICT, CI_FAILURE, ARCHITECTURAL_MISMATCH,
SUPERSEDED, or UNKNOWN.
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv

from github_client import PRData, ReviewData, CheckRunResult

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 512

VALID_CATEGORIES = frozenset(
    ["STALE", "MERGE_CONFLICT", "CI_FAILURE", "ARCHITECTURAL_MISMATCH", "SUPERSEDED", "UNKNOWN"]
)

_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "rca_system.md"


def _load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


@dataclass
class ClassificationResult:
    pr_number: int
    pr_title: str
    category: str
    confidence: float
    reasoning: str
    evidence: list[str]
    # Raw token usage for cost tracking
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int


def _format_reviews(reviews: list[ReviewData]) -> str:
    if not reviews:
        return "None"
    lines = []
    for r in reviews:
        body_preview = r.body[:200].strip() if r.body else ""
        lines.append(f"- [{r.state}] {r.author}: {body_preview}")
    return "\n".join(lines)


def _format_check_runs(check_runs: list[CheckRunResult]) -> str:
    if not check_runs:
        return "None"
    lines = []
    for c in check_runs:
        summary = c.output_summary[:200].strip() if c.output_summary else ""
        lines.append(
            f"- {c.name}: {c.conclusion or c.status}"
            + (f" — {c.output_title}" if c.output_title else "")
            + (f"\n  {summary}" if summary else "")
        )
    return "\n".join(lines)


def _format_comments(comments: list[str], max_chars: int = 2000) -> str:
    if not comments:
        return "None"
    joined = "\n---\n".join(comments)
    if len(joined) > max_chars:
        return joined[:max_chars] + "\n... [truncated]"
    return joined


def _build_user_message(pr: PRData) -> str:
    """Serialize a PRData into a structured plain-text block for the LLM."""
    failed_ci = [c for c in pr.check_runs if c.conclusion in ("failure", "error")]
    return f"""## PR #{pr.number}: {pr.title}

**Author:** {pr.author}
**Created:** {pr.created_at}
**Closed:** {pr.closed_at or "unknown"}
**Labels:** {", ".join(pr.labels) if pr.labels else "none"}

### Description
{pr.body[:500].strip() if pr.body else "No description provided."}

### CI / Check Runs ({len(pr.check_runs)} total, {len(failed_ci)} failed)
{_format_check_runs(pr.check_runs)}

### Reviews ({len(pr.reviews)} total)
{_format_reviews(pr.reviews)}

### Issue Comments ({len(pr.issue_comments)} total)
{_format_comments(pr.issue_comments)}

### Review Comments ({len(pr.review_comments)} total)
{_format_comments(pr.review_comments)}

### Diff (truncated)
{pr.diff[:3000].strip() if pr.diff else "No diff available."}
"""


def _parse_response(raw: str) -> dict:
    """Extract and validate the JSON payload from the model response."""
    text = raw.strip()
    # Strip markdown fences if the model added them despite instructions
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    parsed = json.loads(text)

    category = parsed.get("category", "UNKNOWN")
    if category not in VALID_CATEGORIES:
        category = "UNKNOWN"

    confidence = float(parsed.get("confidence", 0.0))
    confidence = max(0.0, min(1.0, confidence))

    return {
        "category": category,
        "confidence": confidence,
        "reasoning": str(parsed.get("reasoning", "")),
        "evidence": [str(e) for e in parsed.get("evidence", [])],
    }


def classify_pr(
    pr: PRData,
    client: anthropic.Anthropic,
    system_prompt: str,
) -> ClassificationResult:
    """
    Classify a single PR using the Claude API.

    The system prompt is sent with cache_control so it is cached across all
    PR calls in the same batch, reducing cost significantly.
    """
    user_message = _build_user_message(pr)

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                # Cache the stable system prompt across all PR classifications
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    raw_text = response.content[0].text
    usage = response.usage

    try:
        parsed = _parse_response(raw_text)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"  [warning] Failed to parse response for PR #{pr.number}: {e}")
        parsed = {
            "category": "UNKNOWN",
            "confidence": 0.0,
            "reasoning": f"Parse error: {e}. Raw response: {raw_text[:200]}",
            "evidence": [],
        }

    return ClassificationResult(
        pr_number=pr.number,
        pr_title=pr.title,
        category=parsed["category"],
        confidence=parsed["confidence"],
        reasoning=parsed["reasoning"],
        evidence=parsed["evidence"],
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
    )


def classify_prs(
    prs: list[PRData],
    delay_seconds: float = 0.3,
) -> list[ClassificationResult]:
    """
    Classify a list of PRs sequentially with a short delay between requests.

    Args:
        prs: List of PRData objects from the data collector.
        delay_seconds: Pause between API calls to avoid rate limiting.

    Returns:
        List of ClassificationResult objects in the same order as input.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set. Check your .env file.")

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _load_system_prompt()

    results: list[ClassificationResult] = []
    total = len(prs)

    print(f"[classifier] Starting classification of {total} PRs using {MODEL}...")

    for i, pr in enumerate(prs, 1):
        print(f"  [{i}/{total}] PR #{pr.number}: {pr.title[:60]}")
        try:
            result = classify_pr(pr, client, system_prompt)
            results.append(result)
            print(
                f"    -> {result.category} (confidence={result.confidence:.2f}) | "
                f"tokens: in={result.input_tokens} out={result.output_tokens} "
                f"cache_hit={result.cache_read_tokens} cache_create={result.cache_creation_tokens}"
            )
        except (anthropic.APIError, anthropic.APIConnectionError) as e:
            print(f"    [error] API error for PR #{pr.number}: {e}")
            results.append(
                ClassificationResult(
                    pr_number=pr.number,
                    pr_title=pr.title,
                    category="UNKNOWN",
                    confidence=0.0,
                    reasoning=f"API error: {e}",
                    evidence=[],
                    input_tokens=0,
                    output_tokens=0,
                    cache_read_tokens=0,
                    cache_creation_tokens=0,
                )
            )

        if i < total:
            time.sleep(delay_seconds)

    _print_token_summary(results)
    return results


def _print_token_summary(results: list[ClassificationResult]) -> None:
    total_in = sum(r.input_tokens for r in results)
    total_out = sum(r.output_tokens for r in results)
    total_cache_hit = sum(r.cache_read_tokens for r in results)
    total_cache_create = sum(r.cache_creation_tokens for r in results)

    print(
        f"\n[classifier] Token summary — "
        f"input: {total_in} | output: {total_out} | "
        f"cache_hit: {total_cache_hit} | cache_created: {total_cache_create}"
    )


if __name__ == "__main__":
    from github_client import collect_closed_prs

    prs = collect_closed_prs(limit=3)
    results = classify_prs(prs)

    print("\n=== Classification Results ===")
    for r in results:
        print(f"\nPR #{r.pr_number}: {r.pr_title}")
        print(f"  Category   : {r.category}")
        print(f"  Confidence : {r.confidence:.2f}")
        print(f"  Reasoning  : {r.reasoning}")
        print(f"  Evidence   : {r.evidence}")
