# OpenClaw RCA Engine

A pipeline that classifies why closed, unmerged PRs in the [openclaw/openclaw](https://github.com/openclaw/openclaw) repository were abandoned — using the GitHub API for data collection and Claude (Haiku) for LLM-based root cause analysis.

**All code in this repository is AI-generated.** Attribution is tracked at the tool-call level via [GitAI](https://usegitai.com).

---

## Pipeline

```
GitHub API
    │
    ▼
┌─────────────────────┐
│   Data Collector    │  Fetches closed PRs: metadata, comments,
│   (github_client)   │  review threads, CI/CD check runs
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Preprocessor      │  Truncates diffs, formats comment threads,
│                     │  extracts CI failure signals
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   RCA Classifier    │  LLM classification via Claude Haiku.
│   (Claude API)      │  Returns category + reasoning + confidence
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Trend Aggregator  │  Groups by category, computes frequency,
│                     │  writes ranked Markdown report
└─────────────────────┘
```

### Failure categories

| Category | Detection signals |
|---|---|
| `STALE` | Last comment by maintainer requesting changes; no follow-up contributor activity |
| `MERGE_CONFLICT` | CI failure named "conflicts"; diff contains conflict markers |
| `CI_FAILURE` | One or more check runs concluded `failure`; no fix commits after failure |
| `ARCHITECTURAL_MISMATCH` | Review comments flagging design concerns, "out of scope", "wrong direction" |
| `SUPERSEDED` | Closing comment references another PR; label "duplicate" |
| `UNKNOWN` | Insufficient signal to determine root cause; flagged for human review |

---

## Requirements

- Python 3.11+
- GitHub Personal Access Token (public repo read access)
- Anthropic API Key

---

## Setup

```bash
git clone https://github.com/BurningFalls/openclaw-rca-engine.git
cd openclaw-rca-engine

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in GITHUB_TOKEN and ANTHROPIC_API_KEY
```

---

## Usage

### Full pipeline (recommended)

```bash
python src/main.py --limit 20
```

```
[main] Starting RCA pipeline (limit=20)
[github_client] Starting closed PR collection from openclaw/openclaw (limit=20)...
  PR #84514: Update README.md
  PR #55810: sandbox: add workspaceMountPropagation config for Docker wor
  ...
[github_client] Collection complete: 20 closed unmerged PRs
[preprocessor] Preprocessing 20 PRs...
[preprocessor] Done.
[classifier] Starting classification of 20 PRs using claude-haiku-4-5...
  [1/20] PR #84514: Update README.md
    -> CI_FAILURE (confidence=0.85) | tokens: in=1418 out=195 cache_hit=0 cache_create=0
  ...
[classifier] Token summary — input: 82510 | output: 5869 | cache_hit: 0 | cache_created: 0

[main] Done. Report: output/report.md
       20 PRs | 4 categories
       CI/CD Failures: 10 (50.0%)
       Stale / No Contributor Response: 6 (30.0%)
       Superseded by Other PR: 3 (15.0%)
       Unknown: 1 (5.0%)
```

The report is written to `output/report.md`. See [`output/report.md`](output/report.md) for an example from a real run against `openclaw/openclaw`.

### Options

| Flag | Default | Description |
|---|---|---|
| `--limit N` | `20` | Number of closed PRs to fetch |
| `--output PATH` | `output/report.md` | Output path for the Markdown report |

### Run individual stages

```bash
# Collect PRs only
python src/github_client.py

# Classify PRs only (reads from github_client → preprocessor internally)
python src/classifier.py
```

---

## Sample results (20 PRs, 2026-05-20)

| Rank | Category | Count | Share | Avg Confidence |
|------|----------|-------|-------|----------------|
| 1 | CI/CD Failures | 10 | 50.0% | 0.84 |
| 2 | Stale / No Contributor Response | 6 | 30.0% | 0.85 |
| 3 | Superseded by Other PR | 3 | 15.0% | 0.95 |
| 4 | Unknown | 1 | 5.0% | 0.45 |

Key finding: half of all abandoned PRs failed because of unresolved CI failures — specifically, `openclaw/openclaw` requires a "Real behavior proof" check to pass before merge, and contributors frequently abandon PRs rather than supply the proof.

Full report with per-PR reasoning and evidence: [`output/report.md`](output/report.md)

---

## Production design

See [`production_design.md`](production_design.md) for notes on how this pipeline could be deployed and scaled in a production environment — scheduling via GitHub Actions, Docker-based runtime, and token cost optimizations (rule-based pre-classification, model tiering, incremental processing).

---

## Project structure

```
openclaw-rca-engine/
├── README.md
├── ROADMAP.md             # Design decisions and scalability roadmap
├── CLAUDE.md              # Project guidance for Claude Code
├── requirements.txt
├── .env.example
├── prompts/
│   └── rca_system.md      # System prompt for the RCA classifier
├── src/
│   ├── main.py            # CLI entry point
│   ├── github_client.py   # GitHub API data collection
│   ├── preprocessor.py    # Diff truncation and comment formatting
│   ├── classifier.py      # LLM-based RCA classification (Claude Haiku)
│   └── aggregator.py      # Trend grouping and report generation
└── output/
    └── report.md          # Example report from a real run
```

---

## AI attribution

All code was generated by Claude Code. Attribution is tracked at the tool-call level using [GitAI](https://usegitai.com), which hooks into Claude Code's `PreToolUse` and `PostToolUse` events and attaches a Git note to every commit.

```bash
# Install git-ai
curl -fsSL https://usegitai.com/install.sh | bash

# Overall AI percentage
git-ai stats

# Per-line attribution
git-ai blame src/classifier.py
```
