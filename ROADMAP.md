# OpenClaw RCA Engine — Implementation Roadmap

**Challenge:** Agentic Observability & Failure Analysis  
**Goal:** Build tooling that analyzes why PRs fail in the OpenClaw repository, with full AI code attribution from day one.

---

## Design Philosophy

> **"Thin Thread First"** — Ship a small, working end-to-end slice before scaling. Functional logic over perfect setup.

Three core principles guide every decision in this project:

1. **Traceability** — Every AI-generated line is attributed from the moment it's written, not retroactively.
2. **Explainability** — The engine doesn't just classify; it explains *why* with supporting evidence from the PR data.
3. **Operationalizability** — The system is designed to run continuously as part of an engineering workflow, not as a one-off script.

---

## Phase 1 — AI Code Attribution (GitAI)

**Status:** Complete  
**Objective:** Ensure all AI-generated code is tracked from the start of the challenge.

### What was done

- Installed `git-ai` v1.4.11 via the official install script
- Claude Code hooks (`PreToolUse` / `PostToolUse`) were automatically registered in `~/.claude/settings.json`
- Attribution is now attached to every commit as a Git note, surviving rebases and merges

### How to verify

```bash
# View AI attribution stats across commits
git-ai stats

# View per-line AI attribution on a file
git-ai blame <file>
```

### Key decision

Attribution is captured at the tool-call level (every file edit, bash execution), not at commit time. This gives the most granular and accurate AI percentage per PR.

---

## Phase 2 — RCA Engine (Root Cause Analysis)

**Status:** In progress  
**Objective:** Classify why closed, unmerged PRs in the OpenClaw GitHub org were abandoned.

### Architecture overview

```
GitHub API
    │
    ▼
┌─────────────────────┐
│   Data Collector    │  Fetches closed PRs: metadata, comments,
│   (github_client)   │  review threads, CI/CD run results
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Preprocessor      │  Truncates diffs, summarizes comment threads,
│                     │  extracts CI failure messages
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   RCA Classifier    │  LLM-based classification with evidence.
│   (Claude API)      │  Returns category + reasoning + confidence
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Trend Aggregator  │  Groups results, computes frequency,
│                     │  outputs ranked failure trend report
└─────────────────────┘
```

### Failure categories

| Category | Detection signals |
|---|---|
| Stale / No Contributor Response | Last comment by maintainer requesting changes, no follow-up activity for N days |
| Merge Conflicts | CI log contains "merge conflict", diff shows conflict markers |
| CI/CD Failures | Failed check runs, error messages in workflow logs |
| Architectural Mismatch | Reviewer comments referencing design concerns, "out of scope", "wrong direction" |
| Superseded by Other PR | Closing comment references another PR number or "already merged" |

### PoC scope (Thin Thread)

- Target: 20–50 closed PRs from the OpenClaw GitHub org
- Single-pass pipeline: fetch → preprocess → classify → aggregate
- Output: ranked trend report with per-PR evidence

### Expansion path

- Increase PR volume to hundreds with async batch processing
- Add CI log deep-parsing (GitHub Actions API)
- Track trends over time with a lightweight database (SQLite or Supabase)

---

## Phase 3 — Pipeline Integration & Scalability

**Status:** Planned  
**Objective:** Make the system production-ready and cost-efficient.

### Operationalization design

| Concern | Approach |
|---|---|
| **Scheduling** | Run weekly via GitHub Actions cron or a simple cron job |
| **Trigger** | On-demand via CLI + scheduled batch |
| **Output** | Markdown report committed to the repo, or posted as a GitHub issue |
| **Monitoring** | Log classification confidence scores; flag low-confidence results for human review |

### Token cost management

| Strategy | Detail |
|---|---|
| **Preprocessing before LLM** | Truncate diffs to changed signatures only; summarize long comment threads before sending to the model |
| **Prompt caching** | Cache the system prompt and category definitions (stable across all PRs) using Claude's prompt caching |
| **Batch API** | Use Claude's Batch API for large historical runs — up to 50% cost reduction |
| **Confidence threshold** | Only send ambiguous PRs to the LLM; rule-based pre-classifier handles clear-cut cases (e.g., conflict markers in diff) |
| **Model tiering** | Use a fast, cheap model (Haiku) for initial triage; escalate to Sonnet only for complex cases |

### Cost estimate (rough)

| Scale | PRs | Estimated tokens | Estimated cost |
|---|---|---|---|
| PoC | 50 | ~150K | < $0.10 |
| Weekly run | 200 | ~600K | ~$0.30 |
| Full backlog | 2,000 | ~6M | ~$3.00 (with caching) |

---

## Deliverables Checklist

- [x] GitAI installed and Claude Code hooks active
- [x] GitHub data collector implemented
- [x] LLM-based RCA classifier implemented
- [x] Trend aggregator and report generator implemented
- [x] Scalability design document (this file)
- [ ] End-to-end run against OpenClaw closed PRs
- [ ] `README.md` with setup and usage instructions

---

## Repository Structure

```
openclaw-rca-engine/
├── CASE_STUDY.md          # Original challenge brief
├── CLAUDE.md              # Project guidance for Claude Code
├── ROADMAP.md             # This file
├── README.md              # Setup and usage guide
├── .env.example           # Required environment variable template
├── src/
│   ├── github_client.py   # GitHub API data collection
│   ├── preprocessor.py    # Data cleaning and truncation
│   ├── classifier.py      # LLM-based RCA classification
│   ├── aggregator.py      # Trend grouping and report generation
│   └── main.py            # CLI entry point
├── prompts/
│   └── rca_system.md      # System prompt for the classifier
├── output/                # Generated reports (gitignored)
└── requirements.txt
```
