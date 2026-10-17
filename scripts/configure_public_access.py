"""Configure explicitly requested IP access through TLS, preserving private backends.

Run as the authorized LinuxONE host user after installing RHEL nginx. Uses a
short-lived self-signed certificate; verify its fingerprint before trusting it.
No private key or token is printed or copied into this repository.
"""
from pathlib import Path
import subprocess
import tempfile
import json
from datetime import datetime,timezone

def main(root):
    def run(*args):return subprocess.run(list(args),check=True,text=True,capture_output=True)
    def install_text(path,content,mode='644'):
        with tempfile.NamedTemporaryFile('w',delete=False) as f:f.write(content);source=Path(f.name)
        try:run('sudo','install','-m',mode,str(source),path)
        finally:source.unlink()
    run('sudo','install','-d','-m','700','/etc/nginx/continuityguard-tls')
    cert='/etc/nginx/continuityguard-tls/server.crt';key='/etc/nginx/continuityguard-tls/server.key'
    if subprocess.run(['sudo','test','-f',cert]).returncode!=0:
        run('sudo','openssl','req','-x509','-newkey','rsa:3072','-sha256','-days','7','-nodes','-keyout',key,'-out',cert,'-subj','/CN=148.100.99.173','-addext','subjectAltName=IP:148.100.99.173')
        run('sudo','chmod','600',key)
    config='''worker_processes 1;
pid /run/nginx.pid;
error_log /var/log/nginx/continuityguard-error.log warn;
events { worker_connections 256; }
http {
  # Do not log authenticated notebook query URLs or application tokens.
  access_log off;
  server_tokens off;
  map $http_upgrade $cg_connection_upgrade { default upgrade; '' close; }
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_certificate /etc/nginx/continuityguard-tls/server.crt;
  ssl_certificate_key /etc/nginx/continuityguard-tls/server.key;
  client_max_body_size 1m;
  server {
    listen 8888 ssl;
    server_name 148.100.99.173;
    client_max_body_size 20m;
    location / {
      proxy_pass http://127.0.0.1:38888;
      proxy_http_version 1.1;
      proxy_set_header Host $http_host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection $cg_connection_upgrade;
      proxy_buffering off;
      proxy_read_timeout 300;
    }
  }
  server {
    listen 8443 ssl;
    server_name 148.100.99.173;
    location / {
      proxy_pass http://127.0.0.1:8080;
      proxy_http_version 1.1;
      proxy_set_header Host $http_host;
      proxy_set_header X-Forwarded-Proto https;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection $cg_connection_upgrade;
      proxy_buffering off;
      proxy_read_timeout 120;
    }
  }
}
'''
    install_text('/etc/nginx/continuityguard-public.conf',config)
    unit='''[Unit]
Description=ContinuityGuard explicit public TLS access
After=network-online.target
[Service]
Type=simple
ExecStart=/usr/sbin/nginx -c /etc/nginx/continuityguard-public.conf -g "daemon off;"
ExecReload=/usr/sbin/nginx -c /etc/nginx/continuityguard-public.conf -s reload
Restart=on-failure
[Install]
WantedBy=multi-user.target
'''
    install_text('/etc/systemd/system/continuityguard-public.service',unit)
    run('sudo','nginx','-t','-c','/etc/nginx/continuityguard-public.conf')
    # Narrow SELinux grants: only this proxy's two backend port labels. Do not
    # enable the broad httpd_can_network_connect boolean.
    policy_dir=Path('/home/linux1/continuityguard-proxy-policy');policy_dir.mkdir(exist_ok=True)
    source='''module continuityguard_proxy 1.0;
require { type httpd_t; attribute port_type; class tcp_socket name_connect; }
type continuityguard_backend_port_t;
typeattribute continuityguard_backend_port_t port_type;
allow httpd_t continuityguard_backend_port_t:tcp_socket name_connect;
'''
    (policy_dir/'continuityguard_proxy.te').write_text(source)
    run('checkmodule','-M','-m','-o',str(policy_dir/'continuityguard_proxy.mod'),str(policy_dir/'continuityguard_proxy.te'))
    run('semodule_package','-o',str(policy_dir/'continuityguard_proxy.pp'),'-m',str(policy_dir/'continuityguard_proxy.mod'))
    run('sudo','semodule','-i',str(policy_dir/'continuityguard_proxy.pp'))
    # Idempotent label setup, preserving explicit ports rather than a range.
    for port,label in [('8888','http_port_t'),('8080','continuityguard_backend_port_t'),('38888','continuityguard_backend_port_t')]:
        result=subprocess.run(['sudo','semanage','port','-a','-t',label,'-p','tcp',port],capture_output=True)
        if result.returncode:run('sudo','semanage','port','-m','-t',label,'-p','tcp',port)
    run('sudo','touch','/run/nginx.pid');run('sudo','restorecon','/run/nginx.pid')
    rule=['-p','tcp','-m','multiport','--dports','8888,8443','-m','comment','--comment','continuityguard-public-tls','-j','ACCEPT']
    if subprocess.run(['sudo','iptables','-C','INPUT',*rule],capture_output=True).returncode:run('sudo','iptables','-I','INPUT','1',*rule)
    run('sudo','systemctl','daemon-reload');run('sudo','systemctl','reset-failed','continuityguard-public');run('sudo','systemctl','enable','--now','continuityguard-public')
    run('sudo','systemctl','restart','continuityguard-public')
    fingerprint=run('sudo','openssl','x509','-in',cert,'-noout','-fingerprint','-sha256','-dates').stdout
    result={'configured_utc':datetime.now(timezone.utc).isoformat(),'jupyter_url':'https://148.100.99.173:8888/lab','dashboard_url':'https://148.100.99.173:8443','tls':'TLS 1.2/1.3; self-signed short-lived certificate','certificate':fingerprint,'authentication':'Existing separate Jupyter/app tokens retained','private_backends':['127.0.0.1:38888','127.0.0.1:8080'],'verification':'Configuration started; external connectivity must be verified separately','note':'User must verify fingerprint and handle browser trust warning; agent does not bypass certificate interstitials. Do not send tokens over plain HTTP.'}
    root=Path(root);(root/'evidence/public-access.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':
    import sys;main(sys.argv[1])
