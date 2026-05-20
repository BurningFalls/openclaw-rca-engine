"""
GitHub data collector for openclaw/openclaw closed PRs.

Fetches: metadata, comments, review threads, CI/CD check runs.
"""

import os
import time
from dataclasses import dataclass, field
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
    reviews: list[dict]
    check_runs: list[CheckRunResult]


def _fetch_diff(pr: PullRequest) -> Optional[str]:
    """PR diff를 최대 5000자로 잘라서 반환."""
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
                parts.append("\n... [diff truncated]")
                break
            parts.append(chunk)
            total += len(chunk)
        return "\n".join(parts) if parts else None
    except GithubException:
        return None


def _fetch_check_runs(pr: PullRequest) -> list[CheckRunResult]:
    """마지막 커밋의 CI/CD check run 결과를 수집."""
    try:
        commits = list(pr.get_commits())
        if not commits:
            return []
        last_commit = commits[-1]
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


def _fetch_reviews(pr: PullRequest) -> list[dict]:
    """리뷰 상태와 본문을 수집 (APPROVED / CHANGES_REQUESTED / COMMENTED)."""
    try:
        return [
            {
                "author": r.user.login if r.user else "unknown",
                "state": r.state,
                "body": r.body or "",
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            }
            for r in pr.get_reviews()
        ]
    except GithubException:
        return []


def collect_closed_prs(limit: int = DEFAULT_PR_LIMIT) -> list[PRData]:
    """
    openclaw/openclaw의 closed, unmerged PR을 최대 limit개 수집.

    Returns:
        List of PRData objects ready for preprocessing.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.")

    g = Github(token)
    repo = g.get_repo(REPO_NAME)

    collected: list[PRData] = []
    print(f"[github_client] {REPO_NAME}에서 closed PR 수집 시작 (최대 {limit}개)...")

    for pr in repo.get_pulls(state="closed", sort="updated", direction="desc"):
        if len(collected) >= limit:
            break

        # merged PR은 제외 — 우리가 분석할 대상은 abandoned PR
        if pr.merged_at is not None:
            continue

        print(f"  PR #{pr.number}: {pr.title[:60]}")

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

        # GitHub API rate limit 배려
        time.sleep(0.5)

    print(f"[github_client] 수집 완료: {len(collected)}개의 closed unmerged PR")
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
