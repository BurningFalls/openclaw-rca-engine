---
name: git-code-review-apply
description: Fetches inline review comments from a GitHub PR, applies them to the code, and posts a reply to each comment. Use for requests like "/git-code-review-apply 1", "apply review", "reflect code review". Accepts a PR number as argument.
context: fork
---

## Step 0: Validate argument

A PR number must be provided when invoking this skill.

If no PR number is given, stop immediately:

> "Please provide a PR number as an argument. Example: `/git-code-review-apply 1`"

## Step 1: Fetch PR comments

```bash
# Extract repo info
REPO=$(gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"')

# [A] Fetch all inline comments (original comments only, excluding replies)
# Only comments where in_reply_to_id is null are originals
gh api repos/$REPO/pulls/<PR_NUMBER>/comments \
  --jq '[.[] | select(.in_reply_to_id == null)] | .[] | {id: .id, path: .path, line: .original_line, body: .body}'

# Check which original inline comments already have replies (to detect already-processed ones)
gh api repos/$REPO/pulls/<PR_NUMBER>/comments \
  --jq '[.[] | select(.in_reply_to_id != null) | .in_reply_to_id] | unique'

# [B] Fetch all general PR comments (non-inline, PR-level comments)
# Review items that could not be placed inline may appear here
gh api repos/$REPO/issues/<PR_NUMBER>/comments \
  --jq '.[] | {id: .id, body: .body, created_at: .created_at, user: .user.login}'
```

**Important**: Both inline comments ([A]) and general comments ([B]) are candidates for applying. General comments may contain review items that could not be placed inline due to uncertain position — always check them.

## Step 2: Analyze comments and select items to apply

Analyze the fetched comments:

- **Inline comments**: Treat originals that already have a reply as already processed — **exclude** them (prevent duplicate application)
- **General comments**: Extract actionable code change requests from reviewer comments. Exclude comments that indicate completion (e.g., those containing "already applied") — **exclude** them
- Group remaining comments by file
- Understand what each comment is requesting (bug fix, improvement suggestion, style, etc.)

Criteria for marking as non-applicable:
- Already fixed (verify by reading the current file)
- Pure praise or acknowledgement comment

## Step 3: Apply code changes

Modify the relevant files for each applicable comment.

Principles:
- Apply exactly what the comment suggests
- Prefer the suggested code example if provided
- Limit the change scope to the specific issue raised (do not modify surrounding code unnecessarily)

After all changes, verify:
```bash
npx tsc --noEmit && npm run lint && npm test && npm run build
```

If errors occur, re-examine the relevant change and retry.

After verification passes, commit and push automatically:

```bash
git add <modified files>
git commit -m "fix: apply code review — <one-line summary of applied changes>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push
```

**Proceed to Step 4 after push completes.**

## Step 4: Post GitHub replies

Get the commit hash first:

```bash
COMMIT_SHA=$(git rev-parse HEAD)
COMMIT_SHORT=$(git rev-parse --short HEAD)
REPO=$(gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"')
REPO_URL="https://github.com/$REPO"
```

**Inline comments** — post a reply to every original comment regardless of whether it was applied:

```bash
# Applied — include commit link
gh api repos/$REPO/pulls/<PR_NUMBER>/comments/<comment_id>/replies \
  -X POST \
  -f body="Applied. <one-line description of what changed> ($REPO_URL/commit/$COMMIT_SHA)"

# Not applied (already handled, non-applicable, etc.)
gh api repos/$REPO/pulls/<PR_NUMBER>/comments/<comment_id>/replies \
  -X POST \
  -f body="<one-line reason for not applying>"
```

**General comments** — if any items from general comments were applied, post a reply:

```bash
gh api repos/$REPO/issues/<PR_NUMBER>/comments \
  -X POST \
  -f body="## Applied ($REPO_URL/commit/$COMMIT_SHA)\n\n<list of applied items>\n\n<if any items were not applied, list them with reasons>"
```

## Step 5: Report completion

Print a summary to the user when all processing is done:

```
✅ Code review applied
- Comments applied: N
- Comments skipped: N (reason: already processed / not applicable)
- Modified files: [file list]
- tsc/lint/test/build: ✅ passed
- Commit: <commit link>
```
