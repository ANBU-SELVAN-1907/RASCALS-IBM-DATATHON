# Security and deployment boundaries

- The app binds to VM loopback. Access uses SSH or the dedicated TLS proxy on public ports 8443/8888. Backend ports stay private. See PUBLIC-ACCESS.md for certificate verification and the narrow SELinux policy.
- A private random app token creates an HTTP-only SameSite=Strict session cookie. The cookie is marked Secure when the request scheme is HTTPS, including the loopback trusted TLS proxy. HTTP localhost access inside the SSH route remains supported. Public access retains token authentication; production still needs stronger identity and session management.
- API reads except health require a session/bearer token. POST requests require an operator header and matching browser origin when Origin is present. Inputs have bounded batch length, ranges and finite-number validation.
- The ingestion queue has 128 batches, each at most 128 events. Queue saturation returns 429 with visible rejection counters. A deduplication cache retains 5,000 IDs; duplicates older than this retention may be rejected by event-time ordering rather than recognized as duplicates.
- Rolling feature history, in-memory incidents/charts and model caches are bounded. The SQLite telemetry journal retains the most recent 5,000 events. Audit history persists and grows; production needs an archive/retention strategy and disk monitoring.
- The local audit hash chain detects edits to recorded history when its prior head is trusted. A privileged attacker can replace the entire database; this is not an immutable ledger or external signature scheme.
- Model SHA-256 detects mismatch against the supplied manifest. Trusted local joblib files only; it is not safe to load arbitrary model uploads.
- The native deployment uses user 1000, a read-only root filesystem, writable state volume and `/tmp`, all capabilities dropped, and no-new-privileges. Host networking is used to avoid a verified bridge forwarding issue; loopback binding limits exposure but host-network isolation is weaker than a separate network namespace.
- Runtime caps are 2 GiB RAM and 1.5 CPU quota for the app. The lab has its own caps. Containerization and limits were used; this is not a claim of hardware enclave, Secure Execution or pervasive encryption coverage.
- Faults and response actions modify only the simulator, never host processes, real hospital services, SSH settings or shared network controls.
- Raw telemetry is not given unrestricted authority to alter runbooks or execute commands. Local generation has no tools and accepts only validated evidence IDs/wordings.
- This is an event prototype: no authentication-rate limiting, enterprise RBAC, external secret manager, high availability, distributed queue, penetration test, or regulatory certification is claimed.
