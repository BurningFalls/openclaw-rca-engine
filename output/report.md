# OpenClaw RCA — Failure Trend Report

**Generated:** 2026-05-20T08:55:01.187424+00:00  
**Total PRs analyzed:** 20

---

## Failure Category Rankings

| Rank | Category | Count | Share | Avg Confidence |
|------|----------|-------|-------|----------------|
| 1 | CI/CD Failures | 10 | 50.0% | 0.84 |
| 2 | Stale / No Contributor Response | 6 | 30.0% | 0.85 |
| 3 | Superseded by Other PR | 3 | 15.0% | 0.95 |
| 4 | Unknown | 1 | 5.0% | 0.45 |

---

## CI/CD Failures (10 PRs)

**Share:** 50.0%  
**Average confidence:** 0.84

### Top Examples

**PR #84514 — Update README.md**  
Confidence: 0.85  
Reasoning: The PR was closed almost immediately after creation (10 seconds later) with one failed check run labeled 'Real behavior proof: failure'. No reviews or comments exist, and the PR was never updated to address the CI failure, indicating the contributor abandoned it rather than fixing the underlying issue.  
Evidence:
- Check run 'Real behavior proof' concluded with 'failure' status
- PR created and closed within 10 seconds (2026-05-20T08:49:42 to 2026-05-20T08:49:50)
- No review comments, issue comments, or contributor responses after the failure
- No subsequent commits to fix the failing CI check

**PR #40502 — Agents: lower default temperature for tool runs**  
Confidence: 0.85  
Reasoning: The PR has a critical unresolved architectural issue flagged by the greptile code review: `resolveDynamicTemperature` does not guard against Anthropic's extended thinking mode, which requires `temperature: 1`. The review explicitly states this will cause 400 API errors when tools are used with extended thinking enabled. Multiple 'Real behavior proof' CI checks failed, and the greptile review provides a detailed fix showing the function needs modification before it is safe to merge. The contributor has not addressed this blocking feedback.  
Evidence:
- Real behavior proof CI check failed multiple times (6 failures across 89 total checks)
- Greptile review states: 'Anthropic's API requires temperature: 1 when extended thinking is enabled — any other value results in a 400 error'
- Greptile confidence score: 3/5 with explicit statement 'the PR should not be merged as-is for deployments that use extended thinking + tools'
- Review comment provides specific code fix needed: guard resolveDynamicTemperature against active thinking configs
- No test covers the extended-thinking + tool-enabled combination that would fail with this change

**PR #71950 — fix(gateway): guard networkInterfaces calls against sandbox SystemError [AI-assisted]**  
Confidence: 0.85  
Reasoning: The PR had two CI failures: 'check' and 'check-test-types' failed during the initial submission. The maintainer's follow-up comment explicitly states 'the previous CI failure was real' and identifies that `src/infra/network-discovery-display.test.ts` expected warning text when interface discovery fails, but the original PR's approach made those fallbacks silent. The maintainer pushed a fix commit to resolve this test failure, indicating the PR was blocked by unresolved CI issues that required architectural changes to pass validation.  
Evidence:
- Two CI checks failed: 'check' and 'check-test-types'
- Maintainer comment: 'the previous CI failure was real. src/infra/network-discovery-display.test.ts expected warning text when interface discovery fails'
- Maintainer pushed a follow-up commit to fix the test failure by adding an inspection helper to preserve diagnostic warnings
- Original PR's approach of switching only to safeNetworkInterfaces() caused tests to fail due to lost user-facing status diagnostics

## Stale / No Contributor Response (6 PRs)

**Share:** 30.0%  
**Average confidence:** 0.85

### Top Examples

**PR #77965 — fix(feishu): disable ambient proxy inheritance for WebSocket by default**  
Confidence: 0.85  
Reasoning: The PR was closed without being merged despite having passing CI checks and addressing a valid bug fix. The Codex review explicitly stated 'Needs real behavior proof before merge' and identified P2/P3 findings that required contributor action (adding patched-branch proof, env cleanup, changelog, and docs). The review's final statement—'Contributor or maintainer action is needed because automerge cannot supply the missing patched-branch Feishu live proof'—indicates the ball was in the contributor's court. No evidence of follow-up commits, additional proof, or contributor response after the review was found, suggesting the contributor abandoned the PR.  
Evidence:
- Codex review required 'patched-branch Feishu live proof' before merge, marking as blocking
- Review explicitly states: 'Contributor or maintainer action is needed because automerge cannot supply the missing patched-branch Feishu live proof'
- Multiple blockers identified (P2: env cleanup in tests, P3: documentation) awaiting contributor action
- No follow-up commits or contributor comments after the review requirement was posted
- PR closed 3 days after creation with no evidence of addressing the requested proof or blockers

**PR #77437 — fix(gateway): plumb sessionId and onYield through gateway MCP loopback path [AI-assisted]**  
Confidence: 0.85  
Reasoning: The PR was blocked by a required 'Real behavior proof' check that failed, with a clear instruction from the Codex reviewer stating 'Needs real behavior proof before merge' and 'the contributor should update the PR body with proof'. The PR was closed 16 days after creation with no subsequent contributor activity addressing this requirement. The reviewer explicitly noted the missing real-environment proof and the need for contributor action, but no follow-up commits or comments from the contributor are present in the record.  
Evidence:
- Codex review comment states: 'Needs real behavior proof before merge: Missing: the PR body/comments provide manual steps and synthetic/local checks, but no redacted after-fix terminal output, logs, screenshot, recording, or linked artifact from a real claude-cli MCP run'
- Explicit directive: 'the contributor should update the PR body with proof, redacting private details, to trigger re-review'
- Check run 'Real behavior proof' shows failure status
- No subsequent commits or contributor responses after the review feedback
- 16-day gap between PR creation (2026-05-04) and closure (2026-05-20) with no recent activity to address the blocking issue

**PR #78759 — [AI-assisted] fix: prevent shared-secret auth scope escalation on trusted-operator plugin routes**  
Confidence: 0.85  
Reasoning: The PR was closed 13 days after creation with no contributor activity after the automated Codex review requested 'real behavior proof before merge.' The blocking requirement—a real-world gateway/plugin-route proof from an actual setup—was never provided by the author. The review comment explicitly states 'Needs contributor-supplied real behavior proof' and indicates automation should not repair the PR while the proof gate is missing, but there is no evidence the contributor responded or attempted to fulfill this requirement before the PR was closed.  
Evidence:
- Codex review comment: 'Needs real behavior proof before merge' with detailed requirements for contributor-supplied proof
- Review summary explicitly states: 'Needs contributor-supplied real behavior proof plus maintainer/security review' and 'automation should not repair this external PR while the proof gate is missing'
- No review comments or additional contributor responses after the initial Codex review
- PR remained open for 13 days (2026-05-07 to 2026-05-20) without any contributor activity to address the blocking requirement
- Label 'triage: needs-real-behavior-proof' indicates unresolved prerequisite for merge

## Superseded by Other PR (3 PRs)

**Share:** 15.0%  
**Average confidence:** 0.95

### Top Examples

**PR #84033 — fix(cli): node run validates --port loudly (#83923)**  
Confidence: 0.95  
Reasoning: The PR was explicitly closed by a maintainer with a clear statement that it is superseded by PR #84307, which targets the same CLI bug in the same files. The issue comment explicitly directs the canonical review to the other PR and states 'This PR is superseded by an open protected parallel fix that targets the same linked CLI bug and same files.' The maintainer determined that keeping both branches open would split review effort for a single narrow change.  
Evidence:
- Issue comment states: 'This PR is superseded by an open protected parallel fix that targets the same linked CLI bug and same files'
- Closing comment explicitly directs to PR #84307: 'Use https://github.com/openclaw/openclaw/pull/84307 as the canonical branch to review and land one node-run port validation fix'
- Statement: 'So I'm closing this here and keeping the remaining discussion on https://github.com/openclaw/openclaw/pull/84307'
- Both PRs target the same issue (#83923) and modify the same files (src/cli/node-cli/register.ts)
- No CI failures or conflicts present; all checks passed or were skipped

**PR #84469 — fix: Docker setup script prints the full gateway bearer token to stdout**  
Confidence: 0.95  
Reasoning: The PR was explicitly closed by the author in favor of a replacement PR. The closing comment states: 'Closing this PR because I made a submission mistake' and 'Rather than leave confusing review history in place, I am closing this PR and replacing it with a clean PR from a fresh branch linked to the same issue.' The author then explicitly references '#84468' as the replacement PR, directly indicating this PR was superseded.  
Evidence:
- Closing comment: 'Closing in favor of a clean replacement PR linked to #84468.'
- Author explanation: 'This PR was initially opened from a release-pinned branch, which made GitHub show a very large unrelated diff against `main`... Rather than leave confusing review history in place, I am closing this PR and replacing it with a clean PR.'
- No CI failures blocking merge—multiple checks passed including security scans, linting, and type checks
- No review comments or architectural concerns raised
- PR closed immediately (8 minutes after creation) with explicit supersession statement

**PR #84446 — fix: omit api keys from generated models json**  
Confidence: 0.95  
Reasoning: The PR was explicitly closed as superseded by a maintainer who determined that the same credential-persistence fix is already tracked in a more mature PR (#83294). The closing comment states this PR's approach conflicts with the current custom-provider contract and would break non-built-in providers, making the alternative PR the canonical path forward. The maintainer explicitly directs to close this branch and continue through PR #83294.  
Evidence:
- Closing comment: 'This PR should close as superseded: the same Layer 1 credential-persistence work is already tracked in the more mature open PR https://github.com/openclaw/openclaw/pull/83294'
- Maintainer states 'this branch's all-apiKey omission conflicts with the current pi-coding-agent custom-provider contract and would break non-built-in custom providers'
- Explicit direction: 'Close this branch and continue the Layer 1 fix through https://github.com/openclaw/openclaw/pull/83294 or a maintainer-approved successor'
- Security review notes: 'Omitting every apiKey field is not the best fix because it breaks the dependency contract'

## Unknown (1 PR)

**Share:** 5.0%  
**Average confidence:** 0.45

### Top Examples

**PR #58808 — feat: pass requesterSenderId and senderIsOwner to ChannelAgentToolFactory**  
Confidence: 0.45  
Reasoning: The PR shows all CI checks passing (0 failed out of 166 total), no merge conflicts, no review rejections, and no maintainer feedback requesting changes. The Greptile summary gives a strong safety recommendation (5/5 confidence). However, there is no explicit closing comment or label explaining why the PR was closed without merging, and no visible stale activity pattern or architectural concerns in the available data.  
Evidence:
- All 166 CI checks passed with 0 failures
- No review comments or CHANGES_REQUESTED reviews present
- No merge conflict indicators in check runs or comments
- Greptile summary states 'This PR is safe to merge — it is a backward-compatible, additive change with no breaking surface'
- No closing comment visible explaining the reason for closure

---

## Low-Confidence Results (< 0.5) — Flagged for Human Review

- **PR #58808** (UNKNOWN, confidence=0.45): feat: pass requesterSenderId and senderIsOwner to ChannelAgentToolFactory
