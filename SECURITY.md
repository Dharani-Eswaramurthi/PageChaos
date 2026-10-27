# Security policy

PageChaos is an alpha testing library. Use synthetic records and cursors: reports
omit record bodies and raw exception messages, but identities, paths, and cursors
remain visible.

Report vulnerabilities privately through
[GitHub security advisories](https://github.com/Dharani-Eswaramurthi/PageChaos/security/advisories/new).
Do not put credentials or private fixtures in public issues. For ordinary
pagination defects, open a normal issue with a minimal synthetic reproduction.

Only the latest alpha is maintained. There is no guaranteed response time.
The injected HTTPX client is mocked; other clients and subprocesses are outside
interception. Request and record budgets are cooperative, not process timeouts.
