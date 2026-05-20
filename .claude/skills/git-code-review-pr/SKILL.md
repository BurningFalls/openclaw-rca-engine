---
name: git-code-review-pr
description: Posts code review results as inline comments on a GitHub PR. Use for requests like "/git-code-review-pr 1", "post review on PR". Accepts a PR number as argument, calculates diff positions, and posts inline comments via gh api.
context: fork
---

## Step 0: Validate argument

A PR number must be provided when invoking this skill.

If no PR number is given, stop immediately:

> "Please provide a PR number as an argument. Example: `/git-code-review-pr 1`"

## Step 1: Fetch PR info and changed files

```bash
# Extract repo info
gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"'

# PR basic info
gh pr view <PR_NUMBER> --json number,title,headRefName,headRefOid

# Changed files with patch
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/files \
  --jq '.[] | {filename: .filename, patch: .patch}'
```

## Step 2: Analyze current code

Read the changed files and invoke a `code-reviewer` subagent to generate the review.

Context to pass to the subagent:
- Full list of changed files and their patches
- Project stack: Python 3.11+, PyGithub, Anthropic SDK, python-dotenv

## Step 3: Calculate diff positions

Calculate the `position` value per file to place each review item as an inline comment.

Patch hunk parsing rules:
- `@@` header lines are excluded from the position count
- The first line after the header is position 1
- Each `+`, `-`, and ` ` (context) line increments position by 1
- Comments cannot be placed on deleted (`-`) lines — use the adjacent context or added (`+`) line instead

## Step 4: Post inline comments

Post a comment for each review item via gh api:

```bash
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments \
  -X POST \
  -f body="<severity_emoji> **<title>**\n\n<problem description>\n\n<code example if applicable>" \
  -f path="<file path>" \
  -F position=<calculated_position> \
  -f commit_id="<headRefOid>"
```

Severity emojis:
- 🔴 High severity (fix required)
- 🟡 Medium severity (improvement recommended)
- 🟢 Low severity (optional improvement)

If position calculation is uncertain for an item, skip it and post it as a general PR comment at the end:

```bash
gh pr comment <PR_NUMBER> --body "<list of skipped review items>"
```

## Step 5: Report completion

Print a summary to the user after all comments are posted:

```
✅ Code review comments posted
- Inline comments: N
- General comments: N
- PR: <PR URL>

To apply these review comments to the code, run `/git-code-review-apply <PR_NUMBER>`.
```
