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
