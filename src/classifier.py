"""
LLM-based root cause analysis classifier for abandoned pull requests.

Uses the Claude API with prompt caching to classify each PR into one of six
failure categories: STALE, MERGE_CONFLICT, CI_FAILURE, ARCHITECTURAL_MISMATCH,
SUPERSEDED, or UNKNOWN.
"""

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from preprocessor import PreprocessedPR, preprocess_prs

load_dotenv()

__all__ = ["ClassificationResult", "classify_pr", "classify_prs"]

MODEL = "claude-haiku-4-5"
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


def _build_user_message(pr: PreprocessedPR) -> str:
    """Serialize a PreprocessedPR into a structured plain-text block for the LLM."""
    return f"""## PR #{pr.number}: {pr.title}

**Author:** {pr.author}
**Created:** {pr.created_at}
**Closed:** {pr.closed_at or "unknown"}
**Labels:** {", ".join(pr.labels) if pr.labels else "none"}

### Description
{pr.body_truncated}

### CI / Check Runs ({pr.total_ci_count} total, {pr.failed_ci_count} failed)
{pr.check_runs_formatted}

### Reviews ({pr.review_count} total)
{pr.reviews_formatted}

### Issue Comments ({pr.issue_comment_count} total)
{pr.issue_comments_formatted}

### Review Comments ({pr.review_comment_count} total)
{pr.review_comments_formatted}

### Diff (truncated)
{pr.diff_truncated}
"""


def _parse_response(raw: str) -> dict:
    """Extract and validate the JSON payload from the model response."""
    text = raw.strip()
    # Strip optional markdown fences (with or without language tag, handles trailing whitespace)
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    text = text.strip()

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
    pr: PreprocessedPR,
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

    if not response.content:
        raise ValueError("Empty response content from API")
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
    prs: list[PreprocessedPR],
    delay_seconds: float = 0.3,
) -> list[ClassificationResult]:
    """
    Classify a list of preprocessed PRs sequentially with a short delay between requests.

    Args:
        prs: List of PreprocessedPR objects from the preprocessor.
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
        except anthropic.APIError as e:
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

    raw_prs = collect_closed_prs(limit=3)
    prs = preprocess_prs(raw_prs)
    results = classify_prs(prs)

    print("\n=== Classification Results ===")
    for r in results:
        print(f"\nPR #{r.pr_number}: {r.pr_title}")
        print(f"  Category   : {r.category}")
        print(f"  Confidence : {r.confidence:.2f}")
        print(f"  Reasoning  : {r.reasoning}")
        print(f"  Evidence   : {r.evidence}")
