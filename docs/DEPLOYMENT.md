# Verified LinuxONE deployment

The project was trained and tested through Jupyter kernels in the supplied s390x lab container on 17 October 2026. The application then ran in its own native Podman container on the same RHEL 9.8 LinuxONE Community Cloud VM. See `evidence/linuxone-verification.json`, the executed notebooks and `requirements.lock.txt` (a snapshot of the supplied training environment, not a portable cross-platform lock).

## Reproduce

1. Complete the organizer's required labs and confirm the assigned notebook mapping.
2. Place this repository in Jupyter's persistent `shared/continuityguard` directory. Run the five project notebooks, in order, using the supplied Python kernel.
3. Export the repository including generated artifacts to a host directory. Keep private keys, tokens and SQLite state outside the repository.
4. On the LinuxONE host, run `python3 scripts/deploy_linuxone.py /absolute/project/path`. This uses sudo Podman and needs the supplied image available. Port 8080 must be free.
5. Forward VM loopback ports through SSH using the command in the README. Open the app on local port 8080 and Jupyter on 38888. Retrieve the separate application token using the documented Podman command.

## Verified configuration

The application image runs as UID 1000, with 2 GiB memory, 1.5 CPU quota, 256 PID limit, a read-only root, a bounded temporary filesystem, dropped capabilities and no-new-privileges. SQLite and the access token persist in `continuityguard-state`. The app binds only 127.0.0.1:8080. Host networking is an explicit isolation tradeoff. The separately configured TLS proxy admits public 8443/38888 (with 8888 retained as a compatibility alias) while backend ports remain loopback; see PUBLIC-ACCESS.md. Jupyter remains a separate container with its own limits.

The supplied pinned image had mixed OCI-manifest/Docker-layer metadata that caused Podman build to reject its compression MIME type. The deployment script handles this by exporting an **untouched throwaway container** from the pinned image and importing its root filesystem as a local compatibility base, preserving environment/user/workdir. This excludes running lab volumes and credentials. The resulting application image ID is retained in deployment evidence. The compatibility import loses original image-layer provenance; the source digest and procedure remain recorded. Allow sufficient disk for the original image, temporary archive and imported base.

An initial temporary notebook demo occupied port 8080 during deployment. It was stopped, and the standalone application was independently verified running and healthy. The deployment script now checks for port occupancy before build. Do not run a development server on the deployed port; use `CG_PORT=8081` for a separate process.

## Persistence and evidence

`evidence/restart-check.json` records the audit count/head before and after restarting the application container. Persistent audit history survives; live feature windows and browser sessions restart empty. This is a journal-persistence test, not uninterrupted failover or high availability. After restart, run a fresh scenario and sign in again.

The first implementation exceeded a ten-second stop timeout with an open SSE connection. The audit fixed stream/server shutdown bounds and worker/journal cleanup. The latest actual restart with an active SSE client took 3.501 seconds with no forced-kill warning, and retained the original audit prefix. This is a restart/persistence check, not seamless failover.

`evidence/dashboard.png` shows actual local Granite generation and a paired synthetic response preview. `evidence/evaluation.png` shows saved evaluation results. Token-bearing URLs, private keys and patient data are excluded. A local hash chain is not externally signed or tamper-proof: retain its head independently to detect whole-history replacement.

## Performance boundary

Both direct-engine benchmark runs are published. At 100 synthetic service-window events/s, p95 processing per four-event batch was 9.03 ms initially and 53.60 ms in a repeat under competing VM work. Each trial lasted eight seconds with generation off in the benchmark process. Other workloads on the shared VM were not controlled. This excludes HTTP, queue and browser latency and does not establish peak capacity. The actual local Granite explanation took 21.73 seconds; generation is asynchronous and separate from prediction.


## Audited v3 update
Use `--replace` for a deliberate deployment update: build completes first, the prior named app stops, and a stopped rollback container is retained while its state volume is preserved. The latest model version is cg-2026-10-17-v3. `scripts/verify_linuxone.py PROJECT --restart --demo` records actual container properties, an active-client restart and a complete local explanation/response preview without exporting credentials. Host exports from Podman may carry container UID ownership: ensure the host project directories belong to the authorized host user before saving verification files.
