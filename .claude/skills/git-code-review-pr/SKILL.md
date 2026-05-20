---
name: git-code-review-pr
description: 코드 리뷰 결과를 GitHub PR 인라인 코멘트로 작성합니다. "/git-code-review-pr 1", "PR에 리뷰 올려줘" 등의 요청에 사용하세요. PR 번호를 인자로 받아 diff position을 계산한 후 gh api로 인라인 코멘트를 작성합니다.
context: fork
---

## 0단계: 인자 확인

스킬 호출 시 PR 번호가 인자로 제공되어야 합니다.

PR 번호가 없으면 즉시 중단하고 안내합니다:

> "PR 번호를 인자로 제공해주세요. 예: `/git-code-review-pr 1`"

## 1단계: PR 정보 및 변경 파일 확인

```bash
# repo 정보 추출
gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"'

# PR 기본 정보
gh pr view <PR번호> --json number,title,headRefName,headRefOid

# PR 변경 파일 목록과 patch
gh api repos/{owner}/{repo}/pulls/<PR번호>/files \
  --jq '.[] | {filename: .filename, patch: .patch}'
```

## 2단계: 현재 코드 분석

변경된 파일들을 읽고 `code-reviewer` 서브에이전트를 호출하여 리뷰를 생성합니다.

서브에이전트에게 전달할 컨텍스트:
- PR 변경 파일 목록과 patch 전체
- 프로젝트 스택: Next.js 15 App Router, TypeScript, TailwindCSS v4, shadcn/ui, Supabase

## 3단계: diff position 계산

각 지적사항을 인라인 코멘트로 달기 위해 파일별 `position` 값을 계산합니다.

patch hunk 파싱 규칙:
- `@@` 헤더 줄은 position 카운트에서 제외
- patch의 첫 번째 줄(헤더 다음)이 position 1
- `+`, `-`, ` `(컨텍스트) 줄 모두 position을 1씩 증가
- 삭제된(`-`) 줄에는 코멘트를 달 수 없으므로 인접한 컨텍스트 줄이나 추가(`+`) 줄에 달기

## 4단계: 인라인 코멘트 작성

각 지적사항에 대해 gh api로 코멘트를 작성합니다:

```bash
gh api repos/{owner}/{repo}/pulls/<PR번호>/comments \
  -X POST \
  -f body="<심각도이모지> **<제목>**\n\n<문제 설명>\n\n<코드 예시(있는 경우)>" \
  -f path="<파일경로>" \
  -F position=<계산된position> \
  -f commit_id="<headRefOid>"
```

심각도별 이모지:
- 🔴 심각도 높음 (즉시 수정 필요)
- 🟡 심각도 중간 (개선 권장)
- 🟢 심각도 낮음 (선택적 개선)

position 계산이 불확실한 경우 해당 항목은 건너뛰고 마지막에 PR 일반 코멘트로 보완합니다:

```bash
gh pr comment <PR번호> --body "<건너뛴 지적사항 목록>"
```

## 5단계: 완료 보고

작성 완료 후 사용자에게 요약 출력합니다:

```
✅ 코드 리뷰 코멘트 작성 완료
- 인라인 코멘트: N개
- 일반 코멘트: N개
- PR: <PR URL>

리뷰 코멘트를 코드에 반영하려면 `/git-code-review-apply <PR번호>`를 사용하세요.
```
