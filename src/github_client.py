"""
GitHub data collector for openclaw/openclaw closed PRs.

Fetches: metadata, comments, review threads, CI/CD check runs.
"""

import os
import time
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from github import Github, GithubException
from github.PullRequest import PullRequest

load_dotenv()

REPO_NAME = "openclaw/openclaw"
DEFAULT_PR_LIMIT = 50


@dataclass
class CheckRunResult:
    name: str
    status: str
    conclusion: Optional[str]
    output_title: Optional[str]
    output_summary: Optional[str]


@dataclass
class ReviewData:
    author: str
    state: str
    body: str
    submitted_at: Optional[str]


@dataclass
class PRData:
    number: int
    title: str
    state: str
    created_at: str
    closed_at: Optional[str]
    author: str
    body: Optional[str]
    labels: list[str]
    diff: Optional[str]
    issue_comments: list[str]
    review_comments: list[str]
    reviews: list[ReviewData]
    check_runs: list[CheckRunResult]


def _fetch_diff(pr: PullRequest) -> Optional[str]:
    """Fetch the PR diff, truncated to a maximum of 5000 characters."""
    try:
        files = list(pr.get_files())
        parts = []
        total = 0
        for f in files:
            patch = f.patch or ""
            header = f"--- {f.filename} (+{f.additions}/-{f.deletions})\n"
            chunk = header + patch
            if total + len(chunk) > 5000:
                remaining = 5000 - total
                if remaining > len(header):
                    parts.append(header + patch[: remaining - len(header)])
                else:
                    parts.append(header.rstrip())  # at least show which file was truncated
                parts.append("\n... [diff truncated]")
                break
            parts.append(chunk)
            total += len(chunk)
        return "\n".join(parts) if parts else None
    except GithubException:
        return None


def _fetch_check_runs(pr: PullRequest) -> list[CheckRunResult]:
    """Collect CI/CD check run results from the last commit of the PR."""
    try:
        commits = pr.get_commits()
        last_commit = commits[commits.totalCount - 1]
        results = []
        for check_run in last_commit.get_check_runs():
            results.append(
                CheckRunResult(
                    name=check_run.name,
                    status=check_run.status,
                    conclusion=check_run.conclusion,
                    output_title=check_run.output.title if check_run.output else None,
                    output_summary=check_run.output.summary if check_run.output else None,
                )
            )
        return results
    except GithubException:
        return []


def _fetch_reviews(pr: PullRequest) -> list[ReviewData]:
    """Collect review states and bodies (APPROVED / CHANGES_REQUESTED / COMMENTED)."""
    try:
        return [
            ReviewData(
                author=r.user.login if r.user else "unknown",
                state=r.state,
                body=r.body or "",
                submitted_at=r.submitted_at.isoformat() if r.submitted_at else None,
            )
            for r in pr.get_reviews()
        ]
    except GithubException:
        return []


def collect_closed_prs(
    limit: int = DEFAULT_PR_LIMIT,
    repo_name: str = REPO_NAME,
) -> list[PRData]:
    """
    Collect closed, unmerged PRs from the given repository, up to the specified limit.

    Args:
        limit: Maximum number of PRs to collect.
        repo_name: GitHub repository in 'owner/name' format.

    Returns:
        List of PRData objects ready for preprocessing.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN is not set. Check your .env file.")

    with Github(token) as g:
        repo = g.get_repo(repo_name)

        collected: list[PRData] = []
        print(f"[github_client] Starting closed PR collection from {repo_name} (limit={limit})...")

        for pr in repo.get_pulls(state="closed", sort="updated", direction="desc"):
            if len(collected) >= limit:
                break

            # Skip merged PRs — we only analyze abandoned (closed without merge) PRs
            if pr.merged_at is not None:
                continue

            print(f"  PR #{pr.number}: {pr.title[:60]}")

            try:
                issue_comments = [c.body for c in pr.get_issue_comments() if c.body]
                review_comments = [c.body for c in pr.get_review_comments() if c.body]

                data = PRData(
                    number=pr.number,
                    title=pr.title,
                    state=pr.state,
                    created_at=pr.created_at.isoformat(),
                    closed_at=pr.closed_at.isoformat() if pr.closed_at else None,
                    author=pr.user.login if pr.user else "unknown",
                    body=pr.body,
                    labels=[label.name for label in pr.labels],
                    diff=_fetch_diff(pr),
                    issue_comments=issue_comments,
                    review_comments=review_comments,
                    reviews=_fetch_reviews(pr),
                    check_runs=_fetch_check_runs(pr),
                )
                collected.append(data)
            except GithubException as e:
                print(f"  [warning] Skipping PR #{pr.number} due to API error: {e}")
                continue

            # Sleep to respect GitHub API rate limits, except after the last collected PR
            if len(collected) < limit:
                time.sleep(0.5)

        print(f"[github_client] Collection complete: {len(collected)} closed unmerged PRs")
        return collected


if __name__ == "__main__":
    prs = collect_closed_prs(limit=5)
    for pr in prs:
        failed = [c for c in pr.check_runs if c.conclusion == "failure"]
        print(
            f"\nPR #{pr.number} | {pr.author} | labels={pr.labels} | "
            f"reviews={len(pr.reviews)} | CI failures={len(failed)}"
        )
        if pr.issue_comments:
            print(f"  last comment: {pr.issue_comments[-1][:120]!r}")
