# Collection reliability

## Goal confirmation
User authorized repairing collection failures and restarting a test, including creating
fix/collection-reliability. main was clean. Goal: distinguish account failures from
transport failures, recover transient public GET failures, and make stages observable.
Success: targeted regression tests and a fresh Windows Bash execution with honest results.
No credential changes, purchases, TLS verification bypass, or paid POST retries.

## Evidence and implementation slice S1
aisa._post reports raw HTTP failures; latest run has HTTP 402 recharge_required.
sources._trending and breakout._get perform a single public GET; sitemap already retries.
CLI run catches failures but emits no stage progress; daily JSON omits judge failures.
One behavior slice: add a public GET retry utility (3 total attempts, 1/2 second delays,
only transport errors and HTTP 429/5xx; never certificate failures); use in HF/GitHub.
Add actionable 401/402 guidance in AIsa without retries. Add stage start/end progress
and persist judge/tutorial/record results so launcher incomplete checks see their errors.
Files: radar/{http,aisa,sources,breakout,__main__}.py, tests/test_collection_reliability.py,
docs/USER_MANUAL.md and workflow/review artifacts. Existing contracts stay additive.
Tests: transient recovery, nonretryable auth/certificate errors, bounded attempts,
AIsa 401/402 with no retry, progress output and partial-result detection; full pytest.
Live: launch scripts/start-windows.sh with a unique report output path.
No new dependencies or architectural layer beyond a small GET utility.

## Risks
Account balance: requires user action, no purchase authorized. Persistent network/remote
failures may remain: report explicitly, user owns network/provider follow-up. Paid calls
are not retried. Sitemap availability is external and existing retries remain unchanged.
Completion report: changes, tests, live output path, errors and unresolved account needs.
