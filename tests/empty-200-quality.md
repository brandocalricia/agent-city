# Empty HTTP 200 is a failed combo turn

An HTTP 200 with empty content and an output count of 0 is a failed turn for every provider, including when the text is only in the reasoning field.

The combo quality gate returns `HTTP 200 with empty content and output count 0`. On that result the attempt logs:

`Model <model> returned 200 but failed quality check: HTTP 200 with empty content and output count 0`

It then demotes that model only, for 120000 ms, with `recordModelLockoutFailure` reason `empty_content_200`, status 502, exact cooldown 120000. It does not write last-known-good on that path, and it does not mark the provider row failed. The log line is:

`Model <model> demoted for 120000 ms after HTTP 200 with empty content and output count 0`

A response that has visible content still passes.

PASS fake reasoning-only 200 triggered failover: HTTP 200 with empty content and output count 0
PASS streamed reasoning-only 200 triggered failover: HTTP 200 with empty content and output count 0
PASS content HTTP 200 stayed valid

The installed gateway source was patched, then the gateway was reloaded. `tests/empty-200-validateQuality.patch` is the quality-gate diff. `tests/empty_200_failover.mjs` is the check.
