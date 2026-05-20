"""
CLI entry point for the OpenClaw RCA Engine pipeline.

Usage:
    python src/main.py [--limit N] [--output PATH]
"""

import argparse
import sys
from pathlib import Path

from github_client import collect_closed_prs
from classifier import classify_prs
from aggregator import aggregate, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze why closed, unmerged PRs in openclaw/openclaw were abandoned."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of closed PRs to fetch (default: 20)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for the Markdown report (default: output/report.md)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        print(f"[main] Starting RCA pipeline (limit={args.limit})")

        prs = collect_closed_prs(limit=args.limit)
        if not prs:
            print("[main] No PRs collected. Exiting.")
            sys.exit(1)

        results = classify_prs(prs)
        if not results:
            print("[main] No classification results. Exiting.")
            sys.exit(1)

        report = aggregate(results)
        output_path = write_report(report, path=args.output)

        print(f"\n[main] Done. Report: {output_path}")
        print(f"       {report.total_prs} PRs | {len(report.categories)} categories")
        for s in report.categories:
            print(f"       {s.label}: {s.count} ({s.percentage:.1f}%)")
    except (EnvironmentError, OSError) as e:
        print(f"[main] Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
