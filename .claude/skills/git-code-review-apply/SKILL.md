---
name: git-code-review-apply
description: GitHub PR의 인라인 리뷰 코멘트를 fetch하여 코드에 자동으로 반영하고 각 코멘트에 reply를 작성합니다. "/git-code-review-apply 1", "리뷰 반영해줘", "코드 리뷰 반영" 등의 요청에 사용하세요. PR 번호를 인자로 받습니다.
context: fork
---

## 0단계: 인자 확인

스킬 호출 시 PR 번호가 인자로 제공되어야 합니다.

PR 번호가 없으면 즉시 중단하고 안내합니다:

> "PR 번호를 인자로 제공해주세요. 예: `/git-code-review-apply 1`"

## 1단계: PR 코멘트 fetch

```bash
# repo 정보 추출
REPO=$(gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"')

# [A] 인라인 코멘트 전체 조회 (원본 코멘트만, reply 제외)
# in_reply_to_id가 null인 것만 원본 코멘트
gh api repos/$REPO/pulls/<PR번호>/comments \
  --jq '[.[] | select(.in_reply_to_id == null)] | .[] | {id: .id, path: .path, line: .original_line, body: .body}'

# 각 원본 인라인 코멘트에 reply가 달렸는지 확인 (이미 처리됐는지 판단)
gh api repos/$REPO/pulls/<PR번호>/comments \
  --jq '[.[] | select(.in_reply_to_id != null) | .in_reply_to_id] | unique'

# [B] PR 일반 코멘트 전체 조회 (인라인이 아닌 PR 레벨 코멘트)
# position을 특정할 수 없어 인라인으로 달리지 않은 리뷰 항목이 여기에 포함될 수 있음
gh api repos/$REPO/issues/<PR번호>/comments \
  --jq '.[] | {id: .id, body: .body, created_at: .created_at, user: .user.login}'
```

**중요**: 인라인 코멘트([A])와 일반 코멘트([B]) 모두 반영 대상입니다. 일반 코멘트에는 position 계산이 불확실해 인라인으로 달지 못한 리뷰 항목이 포함되어 있을 수 있으므로 반드시 확인해야 합니다.

## 2단계: 코멘트 분석 및 반영 대상 선별

fetch한 코멘트를 분석합니다:

- **인라인 코멘트**: reply가 달린 원본 코멘트는 이미 처리된 것으로 간주하고 **제외** (중복 반영 방지)
- **일반 코멘트**: 리뷰어가 작성한 코멘트 중 코드 수정이 필요한 지적사항을 추출. 이미 반영 완료 코멘트(예: "반영했습니다"가 포함된 것)는 **제외**
- 남은 코멘트를 파일별로 그룹화
- 각 코멘트의 지적사항이 무엇인지 파악 (버그 수정, 개선 제안, 스타일 등)

반영 불가 판단 기준:
- 이미 수정된 상태인 경우 (현재 파일을 읽어 확인)
- 단순 칭찬/확인 코멘트인 경우

## 3단계: 코드 수정 실행

반영 대상 코멘트별로 해당 파일을 수정합니다.

수정 원칙:
- 코멘트에서 제안한 내용을 그대로 적용
- 제안 코드 예시가 있으면 우선 참고
- 수정 범위는 해당 지적사항에 한정 (주변 코드를 불필요하게 변경하지 않음)

모든 수정 완료 후 검증:
```bash
npx tsc --noEmit && npm run lint && npm test && npm run build
```

오류가 발생하면 해당 수정을 재검토 후 재시도합니다.

검증 통과 후 자동으로 커밋하고 push합니다:

```bash
git add <수정된 파일들>
git commit -m "fix: 코드 리뷰 반영 — <반영한 항목 한 줄 요약>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push
```

**push 완료 후 4단계를 진행합니다.**

## 4단계: GitHub reply 작성

커밋 해시를 먼저 확인합니다:

```bash
COMMIT_SHA=$(git rev-parse HEAD)
COMMIT_SHORT=$(git rev-parse --short HEAD)
REPO=$(gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"')
REPO_URL="https://github.com/$REPO"
```

**인라인 코멘트** — 반영 여부에 관계없이 모든 원본 코멘트에 reply를 작성합니다:

```bash
# 반영한 경우 — 커밋 링크 포함
gh api repos/$REPO/pulls/<PR번호>/comments/<코멘트id>/replies \
  -X POST \
  -f body="반영했습니다. <구체적으로 무엇을 바꿨는지 한 줄> ($REPO_URL/commit/$COMMIT_SHA)"

# 반영하지 않은 경우 (이미 처리됨, 반영 불가 등)
gh api repos/$REPO/pulls/<PR번호>/comments/<코멘트id>/replies \
  -X POST \
  -f body="<반영하지 않은 이유 한 줄>"
```

**일반 코멘트** — 반영한 항목이 있으면 해당 코멘트에 답글을 작성합니다:

```bash
gh api repos/$REPO/issues/<PR번호>/comments \
  -X POST \
  -f body="## 반영 완료 ($REPO_URL/commit/$COMMIT_SHA)\n\n<반영한 항목 목록>\n\n<반영하지 않은 항목이 있으면 이유와 함께 명시>"
```

## 5단계: 완료 보고

모든 처리가 끝나면 사용자에게 요약 출력합니다:

```
✅ 코드 리뷰 반영 완료
- 반영한 코멘트: N개
- 건너뛴 코멘트: N개 (이유: 이미 처리됨 / 반영 불가)
- 수정된 파일: [파일 목록]
- tsc/lint/test/build: ✅ 통과
- 커밋: <커밋 링크>
```
