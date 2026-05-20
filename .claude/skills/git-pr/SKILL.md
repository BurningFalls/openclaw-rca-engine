---
name: git-pr
description: Creates a PR from the current branch targeting the main branch. Use for requests like "create a PR", "open a pull request", "git-pr". Assumes the branch is already pushed. Analyzes commits to auto-generate the PR title and body.
context: fork
---

## Step 1: Check current branch

```bash
git branch --show-current
```

If the branch is `main` or `develop`, stop immediately:

> "Cannot create a PR from main/develop. Please run this from a feature branch."

## Step 2: Check commit list

List commits on the current branch that are not on main:

```bash
git log main..HEAD --oneline
```

If there are no commits, stop:

> "No new commits ahead of main."

## Step 3: Determine PR title

Derive the PR title from the branch name.

Branch name pattern: `feat/short-description`

Conversion rules:
- Remove the `feat/`, `fix/`, `chore/` etc. prefix
- Convert kebab-case to readable English
- Add an appropriate type prefix (`feat:`, `chore:`, etc.)

Examples:
- `feat/rca-classifier` → `feat: implement LLM-based RCA classifier`
- `chore/add-claude-settings` → `chore: add Claude Code configuration`

## Step 4: Write PR body

Write the body based on the commit list and changed files.

### Issue number lookup

Extract a task/issue number from the branch name if present:

```bash
ISSUE_NUM=$(gh issue list --search "<keyword from branch>" --json number,title --jq '.[0].number // empty')
```

### Body format

Include `Closes #number` only if an issue number is found; otherwise omit that line:

```markdown
## Summary

- <change bullet 1>
- <change bullet 2>
- <change bullet 3>

## Commits

- `<hash>` <commit message>
- `<hash>` <commit message>

## Test plan

- [ ] <verification item 1>
- [ ] <verification item 2>

Closes #<issue number>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Write the Summary to reflect the purpose of the changes synthesized from the commits (do not just list commit messages verbatim).
Write Test plan items that are practical and specific to the changes.

## Step 5: Prepare metadata

### Get GitHub username

```bash
gh api user --jq '.login'
```

### Prepare labels

Use the branch prefix (`feat`, `fix`, `refactor`, `chore`, `docs`, `test`) as the label name.

Check if the label exists in the repo:

```bash
gh label list --json name --jq '.[].name'
```

If not, create it with the appropriate color:

| tag | color |
|-----|-------|
| `feat` | `0075ca` |
| `fix` | `d73a4a` |
| `refactor` | `e4e669` |
| `chore` | `cfd3d7` |
| `docs` | `0052cc` |
| `test` | `bfd4f2` |

```bash
gh label create "<tag>" --color "<color>" --description "<description>"
```

## Step 6: Create PR

```bash
gh pr create \
  --base main \
  --title "<PR title>" \
  --assignee "<GitHub username>" \
  --label "<branch tag>" \
  --body "$(cat <<'EOF'
<PR body>
EOF
)"
```

## Step 7: Link PR to project

Read `GITHUB_PROJECT_ID` from `.env.local` and add the PR to the project.
Skip this step if `GITHUB_PROJECT_ID` is not set.

```bash
PROJECT_ID=$(grep GITHUB_PROJECT_ID .env.local 2>/dev/null | cut -d '=' -f2-)
if [ -n "$PROJECT_ID" ]; then
  PR_ID=$(gh pr view --json id --jq '.id')
  gh api graphql \
    -f query='mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {
        projectId: $projectId
        contentId: $contentId
      }) { item { id } }
    }' \
    -f projectId="$PROJECT_ID" \
    -f contentId="$PR_ID"
fi
```

## Step 8: Print PR URL

Print the created PR URL to the user.
