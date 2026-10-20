# Collection reliability control
Goal/plan: docs/plans/collection-reliability.md.
Goal confirmation: user authorized repair, branch and restart on 2026-10-20.
Plan review: accepted, no findings; accepted commit 4a04197.
Implementation S1: bounded public GET retries; AIsa account diagnostics; phase progress;
additive daily JSON errors. Code review: docs/reviews/code-review-20261020-165603.md; F1 accepted/fixed/re-reviewed.
Validation: 123 offline tests, Bash syntax and diff checks passed; final rerun pending.
Live Windows Bash run: reports/retest-20261020-165404.md and .log (ignored, local only).
Current gate / next entry point: accepted slice commit after final checks, then aggregate deepreview.
Residual risks: account funding/provider and network availability need external action;
pre-existing nested sitemap exit-code and concurrent report writing assigned to later
work unit (repository maintainer). No secret/config changes, TLS bypass or purchases.

Accepted slice commit: b503d44. Final checks: 123 passed, Bash syntax and diff check pass.
Aggregate deepreview: docs/reviews/code-review-20261020-165715.md; pass-with-risks, no new findings.
Current gate / next entry point: ready-to-open-draft-PR -> push -> create draft PR -> PR review.

Commit identity correction before first successful push (GitHub email privacy):
4a04197 -> a17f155 (plan); b503d44 -> 604bd0d (S1); dbc13e2 -> 45712a8 (aggregate).
Source trees unchanged by identity correction; earlier artifact hashes are historical.
Draft PR: https://github.com/CaryLabs/new-term-radar/pull/2.
PR review: docs/reviews/pr-2-review-20261020-165953.md; pass-with-risks, no new findings; Python 3.10/3.12 CI passed.
Current gate / next entry point: accepted PR review commit -> final push -> draft-PR-pass -> final closeout.

PR review commit 0d7a275 pushed; draft-PR-pass achieved. Final live test ended 17:23:33,
exit 3: HF/GitHub/all 12 sitemaps succeeded; X 32/35 then SSL EOF; judge HTTP 402;
keyword enrichment SSL EOF. See collection-reliability-closeout.md for evidence and
classified external limitations. Final closeout pass for code work, no complete-data
recovery claim. Current gate: completed. Next entry: user/provider account and network
action, then an explicitly requested rerun. PR #2 remains draft/unmerged.
