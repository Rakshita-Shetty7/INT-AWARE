"""
MITRE ATT&CK Mapping Service.
Maps observed attacker intents, stages, and command actions to MITRE ATT&CK Tactics and Techniques.
"""

from typing import Any, Dict, List, Optional, Set
from backend.app.models.intent import IntentCategory, AttackStage


MITRE_INTENT_MAP: Dict[str, Dict[str, Any]] = {
    "RECONNAISSANCE": {
        "tactic": "Reconnaissance",
        "tactic_id": "TA0043",
        "techniques": [
            {"id": "T1592", "name": "Gather Victim Host Information", "url": "https://attack.mitre.org/techniques/T1592/"},
            {"id": "T1046", "name": "Network Service Discovery", "url": "https://attack.mitre.org/techniques/T1046/"},
            {"id": "T1595", "name": "Active Scanning", "url": "https://attack.mitre.org/techniques/T1595/"}
        ]
    },
    "DISCOVERY": {
        "tactic": "Discovery",
        "tactic_id": "TA0007",
        "techniques": [
            {"id": "T1082", "name": "System Information Discovery", "url": "https://attack.mitre.org/techniques/T1082/"},
            {"id": "T1087", "name": "Account Discovery", "url": "https://attack.mitre.org/techniques/T1087/"},
            {"id": "T1083", "name": "File and Directory Discovery", "url": "https://attack.mitre.org/techniques/T1083/"},
            {"id": "T1016", "name": "System Network Configuration Discovery", "url": "https://attack.mitre.org/techniques/T1016/"}
        ]
    },
    "CREDENTIAL_ACCESS": {
        "tactic": "Credential Access",
        "tactic_id": "TA0006",
        "techniques": [
            {"id": "T1110", "name": "Brute Force", "url": "https://attack.mitre.org/techniques/T1110/"},
            {"id": "T1003", "name": "OS Credential Dumping", "url": "https://attack.mitre.org/techniques/T1003/"},
            {"id": "T1552", "name": "Unsecured Credentials", "url": "https://attack.mitre.org/techniques/T1552/"}
        ]
    },
    "EXECUTION": {
        "tactic": "Execution",
        "tactic_id": "TA0002",
        "techniques": [
            {"id": "T1059", "name": "Command and Scripting Interpreter: Unix Shell", "url": "https://attack.mitre.org/techniques/T1059/"},
            {"id": "T1053", "name": "Scheduled Task/Job: Cron", "url": "https://attack.mitre.org/techniques/T1053/"}
        ]
    },
    "PRIVILEGE_ESCALATION": {
        "tactic": "Privilege Escalation",
        "tactic_id": "TA0004",
        "techniques": [
            {"id": "T1548", "name": "Abuse Elevation Control Mechanism: Sudo", "url": "https://attack.mitre.org/techniques/T1548/"},
            {"id": "T1068", "name": "Exploitation for Privilege Escalation", "url": "https://attack.mitre.org/techniques/T1068/"}
        ]
    },
    "PERSISTENCE": {
        "tactic": "Persistence",
        "tactic_id": "TA0003",
        "techniques": [
            {"id": "T1136", "name": "Create Account: Local Account", "url": "https://attack.mitre.org/techniques/T1136/"},
            {"id": "T1547", "name": "Boot or Logon Autostart Execution", "url": "https://attack.mitre.org/techniques/T1547/"},
            {"id": "T1053.003", "name": "Scheduled Task/Job: Cron", "url": "https://attack.mitre.org/techniques/T1053/003/"}
        ]
    },
    "EXPLOITATION": {
        "tactic": "Initial Access",
        "tactic_id": "TA0001",
        "techniques": [
            {"id": "T1190", "name": "Exploit Public-Facing Application", "url": "https://attack.mitre.org/techniques/T1190/"},
            {"id": "T1210", "name": "Exploitation of Remote Services", "url": "https://attack.mitre.org/techniques/T1210/"}
        ]
    },
    "EXFILTRATION": {
        "tactic": "Exfiltration",
        "tactic_id": "TA0010",
        "techniques": [
            {"id": "T1048", "name": "Exfiltration Over Alternative Protocol", "url": "https://attack.mitre.org/techniques/T1048/"},
            {"id": "T1567", "name": "Exfiltration Over Web Service", "url": "https://attack.mitre.org/techniques/T1567/"}
        ]
    },
    "CLEANUP": {
        "tactic": "Defense Evasion",
        "tactic_id": "TA0005",
        "techniques": [
            {"id": "T1070.003", "name": "Indicator Removal: Clear Command History", "url": "https://attack.mitre.org/techniques/T1070/003/"},
            {"id": "T1070.002", "name": "Indicator Removal: Clear Linux System Logs", "url": "https://attack.mitre.org/techniques/T1070/002/"}
        ]
    },
    "OTHER": {
        "tactic": "Initial Access",
        "tactic_id": "TA0001",
        "techniques": [
            {"id": "T1078", "name": "Valid Accounts: Default Credentials", "url": "https://attack.mitre.org/techniques/T1078/"}
        ]
    }
}


class MitreMapper:
    """
    Utility for mapping observed session behaviors to ATT&CK tactics & techniques.
    """

    @classmethod
    def get_techniques_for_intent(cls, intent: str) -> List[Dict[str, Any]]:
        """
        Returns the MITRE techniques associated with an intent category.
        """
        clean_intent = intent.upper()
        mapping = MITRE_INTENT_MAP.get(clean_intent)
        if not mapping:
            return []
        return [
            {
                "tactic": mapping["tactic"],
                "tactic_id": mapping["tactic_id"],
                "technique_id": tech["id"],
                "name": tech["name"],
                "url": tech["url"]
            }
            for tech in mapping["techniques"]
        ]

    @classmethod
    def map_session(cls, session_doc: Dict[str, Any], events: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Aggregates all distinct MITRE ATT&CK techniques observed across a session.
        """
        observed_intents: Set[str] = set()

        # Extract from session intent sequence
        if session_doc.get("intent_sequence"):
            for intent in session_doc["intent_sequence"]:
                if intent:
                    observed_intents.add(intent.upper())

        # Extract from dominant intent
        if session_doc.get("dominant_intent"):
            observed_intents.add(session_doc["dominant_intent"].upper())

        # Extract from individual events if available
        if events:
            for ev in events:
                if ev.get("intent"):
                    observed_intents.add(ev["intent"].upper())

        # Build unique mapped techniques list
        techniques: List[Dict[str, Any]] = []
        seen_tech_ids: Set[str] = set()

        for intent in observed_intents:
            for tech in cls.get_techniques_for_intent(intent):
                if tech["technique_id"] not in seen_tech_ids:
                    seen_tech_ids.add(tech["technique_id"])
                    techniques.append(tech)

        return techniques
