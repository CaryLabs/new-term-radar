# Collection reliability final closeout

## Changes and verification
Bounded retries on public HF/GitHub GETs; actionable AIsa account errors with no billed
POST retries; stderr stage progress; judge/tutorial/record failures preserved in daily
JSON. Manual updated. All 123 tests passed, Bash syntax and diff checks passed.
Python 3.10 and 3.12 GitHub CI passed for source changes. Accepted plan, slice, aggregate
and PR review artifacts are committed. Prior F1 fixed and re-reviewed; no open code findings.

## Actual Windows Bash test
Started 2026-10-20 16:54:04 +08:00; ended 17:23:33; exit 3 (incomplete), 21 candidates.
Local ignored outputs: reports/retest-20261020-165404.md, .json and .log.
HF returned 100 models and 100 Spaces. GitHub returned 200 repositories. All 12 configured
sitemaps succeeded, including toolify (692 URLs); sitemap phase took 1200.9 seconds.
X completed 32/35 accounts, then SSL unexpected EOF at @swyx; vocabulary unchanged.
Name judge returned HTTP 402 recharge_required. Keyword enrichment returned SSL EOF.
Known AIsa data cost $0.090; failed-request/model charges cannot be inferred from this.

## Remaining risks / ownership
- Account balance/model permission: user/AIsa provider; requires account action, cannot
  be repaired in code. No purchases or secret modifications made.
- SSL EOF on paid X/keyword requests: network/provider; assigned to follow-up external
  network/provider investigation. No automatic paid retries or TLS bypass introduced.
  Public-source success does not prove permanent transport reliability.
- Existing nested sitemap exit status and concurrent report publication: assigned to
  later work unit, repository maintainer; no live sitemap error in this test.
- Sitemap runtime: 23 mcp.so shards plus 10 aixploria shards, configured crawl delays;
  performance/coverage tradeoff assigned to later work unit, repository maintainer.

## Delivery
Draft PR https://github.com/CaryLabs/new-term-radar/pull/2; remains draft and unmerged.
No GitHub issue associated with this user request; no issue closeout comment required.
PR review passed; accepted review commit 0d7a275 pushed. Final documentation does not
change production code; reviewed against live test outputs above, no new findings.
Code work unit completed with classified external limitations, final closeout pass.
Full-data service recovery is NOT achieved: account/network limitations remain.
Next entry: user checks AIsa balance/model permission and provider/network EOF; after
that, explicitly rerun collection. PR merge remains a separate user-authorized action.
