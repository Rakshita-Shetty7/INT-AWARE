"""
Beelzebub Decoy Fleet Management and Honeytoken Registry.

Provides enterprise-grade deception infrastructure modeled after Beelzebub Cloud
(beelzebub-labs/beelzebub), supporting low-code YAML decoys across SSH, HTTP, TCP,
Telnet, and Model Context Protocol (MCP) AI agent traps.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DecoyProtocol(str, Enum):
    SSH = "SSH"
    HTTP = "HTTP"
    TCP = "TCP"
    TELNET = "TELNET"
    MCP = "MCP"


class DecoyStatus(str, Enum):
    ONLINE_ACTIVE = "ONLINE_ACTIVE"
    STANDBY = "STANDBY"
    TRIGGERED = "TRIGGERED"
    DEGRADED = "DEGRADED"


class DecoyService(BaseModel):
    decoy_id: str
    name: str
    protocol: DecoyProtocol
    port: int
    status: DecoyStatus
    uptime_hours: float
    interactions_count: int
    honeytokens_tripped: int
    emulation_engine: str
    description: str
    yaml_config: str


class Honeytoken(BaseModel):
    token_id: str
    token_type: str
    label: str
    sample_value: str
    deployed_environment: str
    associated_decoy_id: str
    tripped: bool
    last_tripped_at: Optional[datetime] = None
    trip_count: int = 0
    severity: str
    mitre_technique: str


BEELZEBUB_DEFAULT_DECOYS: List[DecoyService] = [
    DecoyService(
        decoy_id="decoy-ssh-01",
        name="Linux Enterprise Host (OpenSSH)",
        protocol=DecoyProtocol.SSH,
        port=2222,
        status=DecoyStatus.ONLINE_ACTIVE,
        uptime_hours=148.5,
        interactions_count=1240,
        honeytokens_tripped=42,
        emulation_engine="Cowrie / Beelzebub SSH LLM Runtime",
        description="Emulates Debian GNU/Linux 12 with full virtual filesystem (/etc, /var/log, /home/admin) and canary bash history.",
        yaml_config="""apiVersion: "v1"
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
    output: "root:x:0:0:root:/root:/bin/bash\\nadmin:x:1000:1000:Admin:/home/admin:/bin/bash\\nbackup:x:34:34:backup:/var/backups:/usr/sbin/nologin"
  - regex: "^(uname -a|uname)$"
    handler: "terminal"
    output: "Linux corp-bastion-01 6.1.0-18-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.1.76-1 x86_64 GNU/Linux"
tarpit:
  enabled: true
  delayMs: 350
honeytokens:
  - type: "SHADOW_HASH"
    path: "/etc/shadow"
    value: "$2a$12$e8pCanaryRootHashBcryptDeterministicFake2026"
  - type: "AWS_CREDENTIAL"
    path: "/root/.aws/credentials"
    value: "aws_access_key_id=AKIAIOSFODNN7EXAMPLE\\naws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
""",
    ),
    DecoyService(
        decoy_id="decoy-http-api",
        name="Microservices Cloud API & Actuator",
        protocol=DecoyProtocol.HTTP,
        port=8080,
        status=DecoyStatus.ONLINE_ACTIVE,
        uptime_hours=96.2,
        interactions_count=3890,
        honeytokens_tripped=18,
        emulation_engine="Beelzebub HTTP Dynamic Engine",
        description="Simulates Spring Boot / FastAPI backend exposing alluring /actuator/env, /swagger-ui, and Canary JWT tokens.",
        yaml_config="""apiVersion: "v1"
protocol: "http"
address: ":8080"
description: "Cloud Microservices API Gateway Decoy"
serverHeader: "nginx/1.24.0 (Ubuntu)"
routes:
  - path: "/actuator/env"
    method: "GET"
    statusCode: 200
    headers:
      Content-Type: "application/json"
    responseBody: |
      {
        "activeProfiles": ["production", "aws-us-east-1"],
        "propertySources": [
          {"name": "applicationConfig: [classpath:/application.yml]", "properties": {"db.password": "******", "cloud.vault.token": "hvs.CANARY_VAULT_TOKEN_89a"}}
        ]
      }
  - path: "/api/v1/auth/login"
    method: "POST"
    statusCode: 401
    responseBody: '{"status": "error", "message": "Bad credentials. Canary audit log triggered."}'
tarpit:
  enabled: true
  delayMs: 250
""",
    ),
    DecoyService(
        decoy_id="decoy-tcp-redis",
        name="In-Memory Cache Decoy (Redis)",
        protocol=DecoyProtocol.TCP,
        port=6379,
        status=DecoyStatus.ONLINE_ACTIVE,
        uptime_hours=72.0,
        interactions_count=870,
        honeytokens_tripped=9,
        emulation_engine="Beelzebub TCP Custom Responder",
        description="Captures unauthorized unauthorized Redis reconnaissance (INFO, CONFIG GET, KEYS *) with synthetic session keys.",
        yaml_config="""apiVersion: "v1"
protocol: "tcp"
address: ":6379"
description: "Enterprise Redis Cache Decoy"
commands:
  - regex: "^INFO"
    handler: "tcp_raw"
    output: "# Server\\r\\nredis_version:7.0.11\\r\\nos:Linux 6.1.0-18-amd64 x86_64\\r\\n# Keyspace\\r\\ndb0:keys=1420,expires=120,avg_ttl=86400\\r\\n"
  - regex: "^KEYS \\*"
    handler: "tcp_raw"
    output: "*3\\r\\n$18\\r\\nsession:canary_001\\r\\n$21\\r\\nauth:master_api_token\\r\\n$15\\r\\nuser:admin_cache\\r\\n"
""",
    ),
    DecoyService(
        decoy_id="decoy-mcp-agent",
        name="Model Context Protocol (MCP) AI Decoy",
        protocol=DecoyProtocol.MCP,
        port=9090,
        status=DecoyStatus.ONLINE_ACTIVE,
        uptime_hours=48.8,
        interactions_count=415,
        honeytokens_tripped=14,
        emulation_engine="Beelzebub MCP Guardrail Trapper",
        description="Deploys synthetic LLM tool endpoints (execute_command, read_database) to detect prompt injection & agent hijacking.",
        yaml_config="""apiVersion: "v1"
protocol: "mcp"
address: ":9090"
description: "Autonomous Agent Tool Context Trapper"
tools:
  - name: "execute_system_command"
    description: "Executes diagnostic shell commands inside production cluster."
    parameters:
      type: "object"
      properties:
        command: {"type": "string"}
    tripwireAction: "ALERT_IMMEDIATE_PROMPT_INJECTION"
  - name: "query_secure_vault"
    description: "Queries high-privilege secrets vault."
    canaryReturn: "CANARY_MCP_SEC_KEY_994821"
""",
    ),
    DecoyService(
        decoy_id="decoy-telnet-iot",
        name="Edge Gateway / IoT Router (BusyBox)",
        protocol=DecoyProtocol.TELNET,
        port=2323,
        status=DecoyStatus.ONLINE_ACTIVE,
        uptime_hours=120.4,
        interactions_count=5210,
        honeytokens_tripped=31,
        emulation_engine="Beelzebub Telnet Emulation",
        description="Captures automated Mirai and edge botnet brute-force attacks on MIPS BusyBox embedded architecture.",
        yaml_config="""apiVersion: "v1"
protocol: "telnet"
address: ":2323"
description: "Embedded Edge Router Decoy"
banner: "Broadcom MIPS-32 Edge Router V2.4.1 (BusyBox v1.33.1)\\r\\nLogin: "
prompt: "# "
tarpit:
  enabled: true
  delayMs: 500
""",
    ),
]


BEELZEBUB_DEFAULT_HONEYTOKENS: List[Honeytoken] = [
    Honeytoken(
        token_id="tok-aws-01",
        token_type="AWS_IAM_CREDENTIAL",
        label="Production S3 Read/Write IAM Key",
        sample_value="AKIAIOSFODNN7EXAMPLE (Secret: wJalrXUtnFEMI/K7MDENG/...)",
        deployed_environment="Linux Bastion /root/.aws/credentials",
        associated_decoy_id="decoy-ssh-01",
        tripped=True,
        last_tripped_at=datetime.now(timezone.utc),
        trip_count=7,
        severity="CRITICAL",
        mitre_technique="T1552.001 - Credentials in Files",
    ),
    Honeytoken(
        token_id="tok-shadow-02",
        token_type="SHADOW_BCRYPT_HASH",
        label="Root User Bcrypt Shadow Hash",
        sample_value="$2a$12$e8pCanaryRootHashBcryptDeterministicFake2026",
        deployed_environment="Bastion /etc/shadow Decoy",
        associated_decoy_id="decoy-ssh-01",
        tripped=True,
        last_tripped_at=datetime.now(timezone.utc),
        trip_count=23,
        severity="HIGH",
        mitre_technique="T1003.008 - /etc/passwd and /etc/shadow",
    ),
    Honeytoken(
        token_id="tok-db-03",
        token_type="DATABASE_URI",
        label="Primary PostgreSQL Cluster Connection URI",
        sample_value="postgresql://dba_canary:P@ssw0rdCanary2026@10.0.4.12:5432/core_banking",
        deployed_environment="Microservices Decoy /actuator/env",
        associated_decoy_id="decoy-http-api",
        tripped=True,
        last_tripped_at=datetime.now(timezone.utc),
        trip_count=4,
        severity="CRITICAL",
        mitre_technique="T1552.004 - Private Keys and DB Secrets",
    ),
    Honeytoken(
        token_id="tok-fin-04",
        token_type="CORPORATE_TREASURY_IBAN",
        label="Global Capital Wire Escrow IBAN",
        sample_value="US89INTA0000009876543210 (Key: CANARY_FIN_KEY_7a8f9b2c)",
        deployed_environment="Financial Services Security Laboratory",
        associated_decoy_id="decoy-http-api",
        tripped=False,
        trip_count=0,
        severity="HIGH",
        mitre_technique="T1657 - Financial Theft / Wire Fraud",
    ),
    Honeytoken(
        token_id="tok-rag-05",
        token_type="RAG_CANARY_DOCUMENT",
        label="Project Zeus Strategic Acquisition Seed Token",
        sample_value="CANARY_RAG_TOKEN_91e4f2a1",
        deployed_environment="AI Agent Vector Store / Knowledge Base",
        associated_decoy_id="decoy-mcp-agent",
        tripped=True,
        last_tripped_at=datetime.now(timezone.utc),
        trip_count=2,
        severity="HIGH",
        mitre_technique="T1530 - Data from Cloud Storage Object",
    ),
    Honeytoken(
        token_id="tok-ssh-06",
        token_type="SSH_PRIVATE_KEY",
        label="DevOps Deployment RSA Private Key",
        sample_value="-----BEGIN RSA PRIVATE KEY-----\\nCANARY_MIIEowIBAAKCAQEA0...\\n-----END RSA PRIVATE KEY-----",
        deployed_environment="Bastion /home/admin/.ssh/id_rsa",
        associated_decoy_id="decoy-ssh-01",
        tripped=False,
        trip_count=0,
        severity="CRITICAL",
        mitre_technique="T1552.004 - Private Keys",
    ),
]


class BeelzebubFleetManager:
    """Manages decoys, honeytokens, and low-code YAML configurations."""

    def __init__(self) -> None:
        self.decoys: Dict[str, DecoyService] = {d.decoy_id: d for d in BEELZEBUB_DEFAULT_DECOYS}
        self.honeytokens: Dict[str, Honeytoken] = {h.token_id: h for h in BEELZEBUB_DEFAULT_HONEYTOKENS}

    def list_decoys(self) -> List[DecoyService]:
        return list(self.decoys.values())

    def get_decoy(self, decoy_id: str) -> Optional[DecoyService]:
        return self.decoys.get(decoy_id)

    def list_honeytokens(self) -> List[Honeytoken]:
        return list(self.honeytokens.values())

    def record_token_trip(self, token_id: str) -> Optional[Honeytoken]:
        tok = self.honeytokens.get(token_id)
        if tok:
            tok.tripped = True
            tok.trip_count += 1
            tok.last_tripped_at = datetime.now(timezone.utc)
        return tok

    def get_fleet_summary(self) -> Dict[str, Any]:
        decoys = self.list_decoys()
        tokens = self.list_honeytokens()
        return {
            "total_decoys": len(decoys),
            "active_decoys": sum(1 for d in decoys if d.status == DecoyStatus.ONLINE_ACTIVE),
            "total_interactions": sum(d.interactions_count for d in decoys),
            "total_honeytokens": len(tokens),
            "tripped_honeytokens": sum(1 for t in tokens if t.tripped),
            "protocols_supported": ["SSH", "HTTP", "TCP", "TELNET", "MCP"],
            "runtime_engine": "Beelzebub Decoy Runtime 2.4.0 (Hybrid LLM / Rule Sandboxing)",
            "zero_host_execution": True,
        }


beelzebub_fleet_manager = BeelzebubFleetManager()
