---
name: git-pr
description: 현재 브랜치를 기반으로 develop 브랜치 대상 PR을 생성합니다. "PR 만들어줘", "pull request 생성해줘", "git-pr" 등의 요청에 사용하세요. push가 완료된 상태를 가정하며, 커밋 목록을 분석해 PR 제목과 본문을 자동 작성합니다.
context: fork
---

## 1단계: 현재 브랜치 확인

```bash
git branch --show-current
```

브랜치가 `main` 또는 `develop`이면 즉시 중단합니다:

> "main/develop 브랜치에서는 PR을 생성할 수 없습니다. feature 브랜치에서 실행해주세요."

## 2단계: 커밋 목록 확인

develop 브랜치 대비 현재 브랜치의 커밋 목록을 확인합니다:

```bash
git log develop..HEAD --oneline
```

커밋이 없으면 중단합니다:

> "develop 대비 새로운 커밋이 없습니다."

## 3단계: PR 제목 결정

브랜치명에서 PR 제목을 도출합니다.

브랜치명 패턴: `feature/task-001-dev-environment-setup`

변환 규칙:
- `feature/` 접두어 제거
- `task-NNN-` 부분이 있으면 → `Task NNN —` 형식으로 변환
- 나머지 kebab-case를 읽기 좋은 한국어 또는 영문으로 변환
- 적절한 type 접두어(`feat:`, `chore:` 등) 추가

예시:
- `feature/task-001-dev-environment-setup` → `chore: Task 001 — 개발 환경 설정`
- `feature/improve-git-skills` → `chore: git 스킬 개선 및 git-pr 스킬 추가`

## 4단계: PR 본문 작성

커밋 목록과 변경 파일을 바탕으로 본문을 작성합니다.

### 이슈 번호 조회

브랜치명에서 Task 번호를 추출해 연결할 이슈 번호를 찾습니다:

```bash
# 브랜치명 예: feature/task-001-dev-environment-setup → "001" 추출
TASK_NUM=$(git branch --show-current | grep -oE 'task-[0-9]+' | grep -oE '[0-9]+')

if [ -n "$TASK_NUM" ]; then
  ISSUE_NUM=$(gh issue list --search "Task $(printf '%03d' $((10#$TASK_NUM)))" --json number,title --jq '.[0].number // empty')
fi
```

### 본문 형식

`ISSUE_NUM`이 존재하면 `Closes #번호`를 포함하고, 없으면 해당 줄을 생략합니다:

```markdown
## Summary

- <변경사항 bullet 1>
- <변경사항 bullet 2>
- <변경사항 bullet 3>

## Commits

- `<hash>` <커밋 메시지>
- `<hash>` <커밋 메시지>

## Test plan

- [ ] <검증 항목 1>
- [ ] <검증 항목 2>

Closes #<이슈번호>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Summary는 커밋 메시지들을 종합해 변경의 목적 중심으로 작성합니다 (커밋 메시지를 그대로 나열하지 않음).
Test plan은 변경 내용에 맞는 실질적인 검증 항목을 작성합니다.

## 5단계: 메타데이터 준비

### GitHub 사용자명 확인

```bash
gh api user --jq '.login'
```

### 라벨 준비

브랜치 태그(`feature`, `fix`, `refactor`, `chore`, `docs`, `test`)를 라벨명으로 사용합니다.
브랜치명에서 태그를 추출합니다 (예: `feature/task-002-route-skeleton` → `feature`).

해당 라벨이 레포에 존재하는지 확인합니다:

```bash
gh label list --json name --jq '.[].name'
```

라벨이 없으면 태그별 색상으로 생성합니다:

| 태그 | 색상 |
|------|------|
| `feature` | `0075ca` |
| `fix` | `d73a4a` |
| `refactor` | `e4e669` |
| `chore` | `cfd3d7` |
| `docs` | `0052cc` |
| `test` | `bfd4f2` |

```bash
gh label create "feature" --color "0075ca" --description "New feature or request"
gh label create "fix" --color "d73a4a" --description "Bug fix"
gh label create "refactor" --color "e4e669" --description "Code refactoring"
gh label create "chore" --color "cfd3d7" --description "Maintenance or tooling"
gh label create "docs" --color "0052cc" --description "Documentation changes"
gh label create "test" --color "bfd4f2" --description "Test additions or fixes"
```

## 6단계: PR 생성

```bash
gh pr create \
  --base develop \
  --title "<PR 제목>" \
  --assignee "<GitHub 사용자명>" \
  --label "<브랜치 태그>" \
  --body "$(cat <<'EOF'
<PR 본문>
EOF
)"
```

## 7단계: PR을 프로젝트에 연결

`.env.local`에서 `GITHUB_PROJECT_ID`를 읽어 프로젝트에 PR을 추가합니다.
`GITHUB_PROJECT_ID`가 없으면 이 단계를 건너뜁니다.

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

## 8단계: PR URL 출력

생성된 PR URL을 사용자에게 출력합니다.
