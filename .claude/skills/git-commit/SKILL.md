---
name: git-commit
description: Classifies all changes into logical units and commits automatically, regardless of staging state. Use for requests like "commit", "git commit", "commit the changes". Splits into multiple commits when changes span different concerns.
context: fork
---

## Step 1: Check all changes

Run the following commands:

```bash
git status
git diff HEAD
```

Review all changes including both staged and unstaged.

If there are no changes, stop immediately:

> "No changes to commit."

## Step 2: Analyze changes

Read the diff and identify:

- Which files changed (added/modified/deleted)
- What was added/modified/deleted in each file
- The nature of the change (feature, bug fix, config change, etc.)

## Step 3: Classify into logical units

Split into multiple commits when:

- Different types are mixed (e.g., feat + fix, chore + feat)
- File groups serve logically independent purposes (e.g., package install vs config vs cleanup)
- Splitting makes each commit clearer and easier to revert

If a single commit suffices, proceed to Step 4.
If multiple commits are needed, plan the file list and commit message for each unit, then repeat Steps 4–5 for each.

## Step 4: Write commit message

### Format

```
<type>: <subject>

<body>
```

`<body>` is determined automatically:
- Fewer than 3 changed files and simple changes → one-liner, no body
- 3 or more changed files or complex changes → body in bullet format

### Type selection

| type | when to use |
|------|-------------|
| `feat` | new feature |
| `fix` | bug fix |
| `docs` | documentation only (no code change) |
| `style` | formatting, missing semicolons, etc. (no functional change) |
| `refactor` | refactoring (neither feature nor bug fix) |
| `test` | adding or modifying tests |
| `chore` | build, dependencies, config files, etc. |
| `perf` | performance improvement |

### Writing rules

- subject: under 50 chars, imperative mood, no period
- body lines: under 72 chars each
- Good: `feat: add user profile image upload`
- Bad: `fix: fix bug` (vague), `feat: add login and fix bug` (two concerns mixed)

## Step 5: Stage and commit

Stage the files for this unit and commit:

```bash
git add <file1> <file2> ...
git commit -m "$(cat <<'EOF'
<type>: <subject>

<body>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Repeat this step for each unit if multiple commits are needed.

## Step 6: Report completion

Summarize the created commits:

```bash
git log --oneline -<commit count>
```

Print commit hashes and messages in a table.
