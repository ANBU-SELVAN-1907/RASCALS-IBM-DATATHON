# Open the actual LinuxONE VM by IP

- JupyterLab: **https://148.100.99.173:8888/lab**
- ContinuityGuard: **https://148.100.99.173:8443**

These are authenticated TLS frontends on the LinuxONE VM. Nginx forwards to the existing loopback backends: Jupyter 38888 and application 8080. Both public endpoints were reached from the participant's computer with the certificate verified; see `evidence/public-connectivity.json`. A localhost SSH URL is also valid: it forwards to the same IBM VM and does not mean inference runs on the laptop.

## If you see “plain HTTP request was sent to HTTPS port”

Open the complete **https://148.100.99.173:8888/lab** address in Chrome. Port 8888 expects TLS. The proxy now redirects accidental plain HTTP requests on ports 8888/8443 to their fixed HTTPS addresses using status 308, rather than showing nginx's 400 page. The deployed configuration and successful HTTPS requests are checked in `evidence/http-https-redirect.json`. Enter credentials only after reaching verified HTTPS. If an embedded browser or network proxy still shows this error, open the exact HTTPS address directly in Chrome or use the documented SSH tunnel.

## Certificate trust

The short-lived certificate is self-signed and expires on **24 October 2026**. Chrome will show a certificate warning. Before entering a token, inspect the certificate and verify this SHA-256 fingerprint:

```text
3F:E1:FD:8C:62:B1:75:73:60:70:92:5A:7A:4D:E0:20:B9:F2:93:F4:BC:07:0E:D4:B3:89:A0:2E:7E:28:54:B4
```

The browser trust decision must be completed manually by the user. No browser warning was bypassed by the agent. Do not use plain `http://148.100.99.173:8888` or send tokens in public URLs/screenshots. An issued certificate for a controlled domain is preferable for longer use.

## Authentication

Use the existing Jupyter token at its login form. The dashboard uses a different application token. Retrieve credentials through the private SSH session or the earlier private handoff, never from GitHub. Jupyter authentication and CSRF protection remain enabled. The proxy supports notebook WebSockets and the app's streaming connection. Proxy access logging is disabled so notebook query tokens are not recorded there.

## Administration

The dedicated service is `continuityguard-public.service`; its configuration is `/etc/nginx/continuityguard-public.conf`. A narrow SELinux module allows proxy connections only to the two specifically labeled backend ports. The broad outbound-network boolean remains off. Explicit host firewall rules admit TLS ports 8888/8443. Those direct iptables rules may require reapplication after host/network reset; the script is idempotent. SELinux and token authentication were not disabled.

The TLS private key stays under `/etc/nginx/continuityguard-tls/`, outside the project. After judging, stop the public proxy and remove its specifically named firewall rule if public access is no longer needed; preserve notebooks, models and journal. Do not delete the only lab volume or required model. No indiscriminate VM cleanup was performed.

## Reproduce proxy configuration

On RHEL install `nginx`, `policycoreutils-python-utils`, `checkpolicy` and `policycoreutils-devel`. In the persistent Jupyter server configuration enable `c.ServerApp.allow_remote_access = True` and `c.ServerApp.trust_xheaders = True` for the trusted loopback proxy, retaining token and CSRF settings, then restart Jupyter. Run `python3 scripts/configure_public_access.py /absolute/project/path` on the host. Inspect its narrow port policy before applying it on another host; the published IP is this assigned VM. Verify the new certificate fingerprint and both authenticated services. Do not copy private keys or access tokens into the project.
