# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

OpenClaw RCA Engine — classifies why closed, unmerged PRs in the `openclaw/openclaw` GitHub repository were abandoned. Pipeline: GitHub API → Data Collector → Preprocessor → RCA Classifier (Claude API) → Trend Aggregator.

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in both keys
```

Required env vars (in `.env`):
- `GITHUB_TOKEN` — fine-grained PAT, public repo read access is sufficient
- `ANTHROPIC_API_KEY` — used by the RCA classifier

## Running the Pipeline

```bash
# Fetch closed PRs from openclaw/openclaw (PoC: 5 PRs)
python src/github_client.py

# Classify PRs with Claude Haiku (PoC: 3 PRs) — requires ANTHROPIC_API_KEY
python src/classifier.py
```

## Architecture

- `src/github_client.py` — fetches closed unmerged PRs (metadata, comments, review threads, CI results)
- `src/classifier.py` — LLM classification via Claude Haiku; returns category + reasoning + confidence score
- `prompts/rca_system.md` — system prompt for the classifier; loaded relative to `src/` via `Path(__file__).parent.parent / "prompts"`
- `output/` — generated reports (gitignored)

Planned but not yet implemented: `preprocessor.py`, `aggregator.py`, `main.py` (see `ROADMAP.md`).

## Prompt Caching

The system prompt is cached after the first PR call. Subsequent PRs in the same run read from cache (`cache_hit` tokens), significantly reducing cost. Preserve the `cache_control` block on the system prompt when modifying `classifier.py`.

## RCA Categories

Defined in `prompts/rca_system.md`. Do not hardcode category names in source — always reference the prompt file as the source of truth.

## Commit Style

Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`. Branch names: `feat/<short-description>`.
