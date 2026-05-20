# Pipeline Integration & Scalability

## Production Workflow Design

### Pipeline

The pipeline runs periodically and follows the workflow below.

```text
1. Fetch recently closed PRs from the GitHub API
2. Preprocess PR data
3. Run LLM-based RCA classification
4. Aggregate classification results
5. Generate and upload report.md
```

The analysis result is generated as a markdown report so it can be viewed directly inside the GitHub repository.

---

### Scheduling

The pipeline can be executed using a GitHub Actions cron schedule.

```yaml
on:
  schedule:
    - cron: "0 9 * * 1"
  workflow_dispatch:
```

A weekly batch schedule was chosen for the following reasons:

- The project does not have a very large PR volume.
- Weekly trend analysis is sufficient for identifying meaningful patterns.
- Running the pipeline too frequently may result in unnecessary repeated analysis.

`workflow_dispatch` can also be enabled to allow manual execution when needed.

---

### Deployment & Runtime Environment

The runtime environment can be containerized using Docker.

Running the same container inside the GitHub Actions runner helps:

- reduce differences between local/dev/prod environments
- prevent dependency mismatch issues

The pipeline can be reproduced consistently with:

```bash
docker compose up --build
```

---

## Token Cost Optimization Strategies

### 1. Rule-based Pre-classifier (`rule_classifier.py`)

Simple and obvious PRs can be classified using rule-based logic before making any LLM API calls.

Examples:
- failed CI check → `CI_FAILURE`
- conflict marker detected → `MERGE_CONFLICT`
- duplicate label detected → `SUPERSEDED`

This can reduce unnecessary API calls and lower overall token costs.

---

### 2. Model Tiering (Haiku → Sonnet)

Instead of using a high-cost model for every PR, the system can use:

- Haiku for most PRs
- Sonnet only for low-confidence classifications

This approach keeps the average cost low while still allowing more complex PRs to be analyzed with a stronger model.

---

### 3. Incremental Processing

Reprocessing all PRs on every run increases both execution time and token cost.

To avoid this, the system can store the timestamp of the last processed PR in a state file.

```json
{
  "last_closed_at": "2026-05-18T14:23:11Z"
}
```

Future runs only fetch PRs closed after this timestamp, which helps prevent duplicate analysis and reduces unnecessary LLM usage.

