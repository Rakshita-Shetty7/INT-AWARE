"""
Deterministic Rule-Based Intent Classifier.
Evaluates observed commands, event types, and behavioral patterns against transparent heuristic rules.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from backend.app.models.events import NormalizedEvent
from backend.app.models.features import SessionFeatures
from backend.app.models.intent import AttackStage, IntentCategory, RuleClassification


@dataclass
class RuleDefinition:
    rule_id: str
    name: str
    intent: IntentCategory
    attack_stage: AttackStage
    confidence: float
    command_patterns: List[str]
    event_types: List[str]
    description: str


# Configurable Rule Definitions
RULES_CATALOG: List[RuleDefinition] = [
    # --- CREDENTIAL ACCESS RULES ---
    RuleDefinition(
        rule_id="RULE_CRED_01",
        name="Failed Authentication Attempt",
        intent=IntentCategory.CREDENTIAL_ACCESS,
        attack_stage=AttackStage.CREDENTIAL_ACCESS,
        confidence=0.85,
        command_patterns=[],
        event_types=["login_failed"],
        description="Observed failed login attempt indicating potential credential brute-forcing or dictionary attack"
    ),
    RuleDefinition(
        rule_id="RULE_CRED_02",
        name="Shadow / Secret Key Access",
        intent=IntentCategory.CREDENTIAL_ACCESS,
        attack_stage=AttackStage.CREDENTIAL_ACCESS,
        confidence=0.95,
        command_patterns=[
            r"cat\s+.*(/etc/shadow|/etc/gshadow)",
            r"cat\s+.*(\.ssh/id_rsa|\.ssh/id_ed25519|\.ssh/id_ecdsa)",
            r"cat\s+.*(\.bash_history|\.sh_history|\.zsh_history)",
            r"grep\s+(-i\s+)?(pass|pwd|secret|key|token|auth)"
        ],
        event_types=["command_input", "command_failed"],
        description="Attempt to read sensitive credential stores or cryptographic private keys"
    ),

    # --- PRIVILEGE ESCALATION RULES ---
    RuleDefinition(
        rule_id="RULE_PRIVESC_01",
        name="Superuser Switching & Sudo Enumeration",
        intent=IntentCategory.PRIVILEGE_ESCALATION,
        attack_stage=AttackStage.PRIVILEGE_ESCALATION,
        confidence=0.92,
        command_patterns=[
            r"^sudo\s+(-i|-s|su|/bin/bash|/bin/sh)",
            r"^su(\s+-|\s+root|\s*$)",
            r"^sudo\s+-l",
            r"^pkexec\s+",
            r"^doas\s+"
        ],
        event_types=["command_input", "command_failed"],
        description="Execution of privileged switching commands or sudo capability enumeration"
    ),
    RuleDefinition(
        rule_id="RULE_PRIVESC_02",
        name="SUID / SGID Binary Search",
        intent=IntentCategory.PRIVILEGE_ESCALATION,
        attack_stage=AttackStage.PRIVILEGE_ESCALATION,
        confidence=0.90,
        command_patterns=[
            r"find\s+/\s+.*-perm\s+(-4000|-u=s|-2000)",
            r"chmod\s+(\+s|[0-7]?[4-7][0-7]{2})"
        ],
        event_types=["command_input", "command_failed"],
        description="Searching for or configuring SUID permissions for local privilege escalation"
    ),

    # --- EXECUTION RULES ---
    RuleDefinition(
        rule_id="RULE_EXEC_01",
        name="Remote Script Download & Pipe to Shell",
        intent=IntentCategory.EXECUTION,
        attack_stage=AttackStage.EXECUTION,
        confidence=0.95,
        command_patterns=[
            r"(curl|wget|fetch|tftp).*(http|ftp).*\|\s*(sh|bash|zsh|python|perl)",
            r"(curl|wget)\s+.*(-O|--output).*;\s*(chmod\s+\+x|sh|bash|\./)",
            r"bash\s+-i\s+>&?\s+/dev/tcp/",
            r"nc\s+.*-e\s+(/bin/sh|/bin/bash)"
        ],
        event_types=["command_input", "command_failed"],
        description="Payload dropper or reverse shell one-liner executing remote script in shell"
    ),
    RuleDefinition(
        rule_id="RULE_EXEC_02",
        name="Inline Interpreter Execution",
        intent=IntentCategory.EXECUTION,
        attack_stage=AttackStage.EXECUTION,
        confidence=0.88,
        command_patterns=[
            r"python[23]?\s+-c\s+['\"].*(import\s+(socket|os|subprocess|pty))",
            r"perl\s+-e\s+['\"].*use\s+Socket",
            r"ruby\s+-e\s+['\"].*require\s+'socket'"
        ],
        event_types=["command_input", "command_failed"],
        description="Executing inline scripting payload targeting sockets or subprocess spawning"
    ),

    # --- PERSISTENCE RULES ---
    RuleDefinition(
        rule_id="RULE_PERSIST_01",
        name="Cron & Scheduled Task Tampering",
        intent=IntentCategory.PERSISTENCE,
        attack_stage=AttackStage.PERSISTENCE,
        confidence=0.90,
        command_patterns=[
            r"crontab\s+(-e|-l|/tmp/.*)",
            r"echo\s+.*>>\s*(/etc/crontab|/var/spool/cron|/etc/cron\.)",
            r"systemctl\s+enable\s+",
            r"chkconfig\s+.*\s+on"
        ],
        event_types=["command_input", "command_failed"],
        description="Modifying crontabs or system services to maintain persistent access"
    ),
    RuleDefinition(
        rule_id="RULE_PERSIST_02",
        name="SSH Authorized Keys Modification",
        intent=IntentCategory.PERSISTENCE,
        attack_stage=AttackStage.PERSISTENCE,
        confidence=0.95,
        command_patterns=[
            r"echo\s+.*(ssh-rsa|ssh-ed25519|ecdsa-sha2).*>>\s*.*authorized_keys",
            r"(useradd|adduser)\s+.*(-G\s+sudo|-G\s+wheel|--uid\s+0)"
        ],
        event_types=["command_input", "command_failed"],
        description="Injecting rogue SSH public keys or creating administrative backdoor accounts"
    ),

    # --- EXFILTRATION RULES ---
    RuleDefinition(
        rule_id="RULE_EXFIL_01",
        name="Data Archive & Outbound Transfer",
        intent=IntentCategory.EXFILTRATION,
        attack_stage=AttackStage.EXFILTRATION,
        confidence=0.88,
        command_patterns=[
            r"(tar|zip|gzip|7z)\s+.*-c.*(/etc|/home|/var/log|/root)",
            r"curl\s+.*(-X\s+POST|--upload-file|-F\s+file=@)",
            r"(scp|rsync)\s+.*@.*:",
            r"nc\s+.*<.*(/etc/passwd|/etc/shadow|\.sql|\.db)"
        ],
        event_types=["command_input", "command_failed"],
        description="Archiving sensitive directories or exfiltrating data via network utilities"
    ),

    # --- CLEANUP RULES ---
    RuleDefinition(
        rule_id="RULE_CLEAN_01",
        name="Log Wiping & History Erasure",
        intent=IntentCategory.CLEANUP,
        attack_stage=AttackStage.CLEANUP,
        confidence=0.92,
        command_patterns=[
            r"history\s+(-c|-w)",
            r"(rm|shred)\s+.*(\.bash_history|\.zsh_history|/var/log/)",
            r"unset\s+HISTFILE",
            r"export\s+HISTSIZE=0"
        ],
        event_types=["command_input", "command_failed"],
        description="Covering tracks by erasing shell history or wiping system log files"
    ),

    # --- EXPLOITATION RULES ---
    RuleDefinition(
        rule_id="RULE_EXPLOIT_01",
        name="Known Vulnerability & Exploit Patterns",
        intent=IntentCategory.EXPLOITATION,
        attack_stage=AttackStage.EXECUTION,
        confidence=0.92,
        command_patterns=[
            r"\(\)\s*\{\s*:\s*;\s*\}\s*;",  # Shellshock pattern
            r"(CVE-\d{4}-\d+|dirtycow|overlayfs|pwnkit)"
        ],
        event_types=["command_input", "command_failed"],
        description="Payload signatures matching known exploitation attempts or vulnerability probes"
    ),

    # --- RECONNAISSANCE RULES ---
    RuleDefinition(
        rule_id="RULE_RECON_01",
        name="System & User Reconnaissance",
        intent=IntentCategory.RECONNAISSANCE,
        attack_stage=AttackStage.RECONNAISSANCE,
        confidence=0.88,
        command_patterns=[
            r"^(whoami|id|hostname|arch|uname(\s+-[a-zA-Z]+)?)$",
            r"^cat\s+.*(/etc/issue|/etc/os-release|/etc/debian_version|/etc/redhat-release)",
            r"^(w|who|uptime|last(\s+-[0-9]+)?)$",
            r"^lscpu$"
        ],
        event_types=["command_input", "command_failed"],
        description="Querying system identity, OS version, kernel release, or current user context"
    ),

    # --- DISCOVERY RULES ---
    RuleDefinition(
        rule_id="RULE_DISC_01",
        name="Network, Process & File Discovery",
        intent=IntentCategory.DISCOVERY,
        attack_stage=AttackStage.DISCOVERY,
        confidence=0.85,
        command_patterns=[
            r"^(ls|dir)(\s+-[a-zA-Z0-9]+)?(\s+.*)?$",
            r"^(find\s+|which\s+|whereis\s+)",
            r"^(ps|top|htop)(\s+.*)?$",
            r"^(netstat|ss|ip\s+a|ip\s+r|ifconfig|arp|route)(\s+.*)?$",
            r"^cat\s+.*(/etc/passwd|/etc/hosts|/etc/resolv.conf|/proc/cpuinfo|/proc/version|/proc/net/)"
        ],
        event_types=["command_input", "command_failed"],
        description="Scanning internal filesystem structures, network routes, active sockets, or process lists"
    ),
]


class RuleClassifier:
    """
    Evaluates normalized honeypot events against transparent deterministic rules.
    """

    def __init__(self, rules: Optional[List[RuleDefinition]] = None):
        self.rules = rules if rules is not None else RULES_CATALOG

    def classify(
        self,
        event: NormalizedEvent,
        session_features: Optional[SessionFeatures] = None
    ) -> RuleClassification:
        """
        Evaluates the event against the rule catalog and returns a RuleClassification.
        """
        matched_rules: List[RuleDefinition] = []
        evidence_list: List[str] = []

        cmd = (event.command or "").strip()
        ev_type = event.event_type

        for rule in self.rules:
            rule_matched = False

            # Check event type matching
            if rule.event_types and ev_type in rule.event_types:
                if not rule.command_patterns:
                    # Pure event type match (e.g. login_failed)
                    rule_matched = True
                    evidence_list.append(f"Event type '{ev_type}' matched {rule.name} ({rule.description})")
                elif cmd:
                    # Match command against regex patterns
                    for pattern in rule.command_patterns:
                        if re.search(pattern, cmd, re.IGNORECASE):
                            rule_matched = True
                            evidence_list.append(
                                f"Command '{cmd}' matched pattern '{pattern}' under {rule.name} ({rule.description})"
                            )
                            break

            if rule_matched:
                matched_rules.append(rule)

        # If matching rules found, select the highest confidence / highest severity rule
        if matched_rules:
            # Sort by confidence descending
            best_rule = max(matched_rules, key=lambda r: r.confidence)
            return RuleClassification(
                intent=best_rule.intent,
                attack_stage=best_rule.attack_stage,
                confidence=best_rule.confidence,
                rule_matches=[r.rule_id for r in matched_rules],
                evidence=evidence_list
            )

        # Fallback handling based on basic event types
        if ev_type == "login_success":
            return RuleClassification(
                intent=IntentCategory.OTHER,
                attack_stage=AttackStage.INITIAL_ACCESS,
                confidence=0.70,
                rule_matches=["RULE_INITIAL_ACCESS"],
                evidence=["Successful session authentication established"]
            )
        elif ev_type in ("session_connect", "client_version", "client_kex", "client_size", "session_params"):
            return RuleClassification(
                intent=IntentCategory.OTHER,
                attack_stage=AttackStage.INITIAL_ACCESS,
                confidence=0.50,
                rule_matches=["RULE_SESSION_HANDSHAKE"],
                evidence=[f"Session connection telemetry: {ev_type}"]
            )
        elif ev_type == "session_closed":
            return RuleClassification(
                intent=IntentCategory.OTHER,
                attack_stage=AttackStage.UNKNOWN,
                confidence=0.50,
                rule_matches=["RULE_SESSION_CLOSE"],
                evidence=["Session connection terminated"]
            )

        # Default fallback for unmapped commands/events
        return RuleClassification(
            intent=IntentCategory.OTHER,
            attack_stage=AttackStage.UNKNOWN,
            confidence=0.30,
            rule_matches=[],
            evidence=[f"No specific rule matched command: '{cmd or ev_type}'"]
        )
