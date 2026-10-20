"""
Financial Services Security Laboratory Engine.

Simulates core banking decoy endpoints, monitors canary financial credentials,
detects automated wire diversion and fraudulent account manipulation, and generates
forensic financial incident reports.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.app.research.financial_lab.models import (
    AccountType,
    FinancialAccount,
    FinancialIncidentReport,
    FinancialTransferRequest,
)

logger = logging.getLogger(__name__)


# Default synthetic decoy bank accounts
SYNTHETIC_BANK_ACCOUNTS: List[FinancialAccount] = [
    FinancialAccount(
        account_id="acc_treasury_01",
        account_number="9876543210",
        iban="US89INTA0000009876543210",
        account_type=AccountType.CORPORATE_TREASURY,
        balance=4520000.00,
        currency="USD",
        holder_name="Global Capital Treasury Holding LLC",
        is_canary=True,
        canary_token="CANARY_FIN_KEY_7a8f9b2c",
        security_flag="CANARY_ACTIVE_HONEYPOT",
    ),
    FinancialAccount(
        account_id="acc_escrow_02",
        account_number="1234567890",
        iban="US44INTA0000001234567890",
        account_type=AccountType.ESCROW,
        balance=1850000.50,
        currency="USD",
        holder_name="Consolidated Merchant Escrow Trust",
        is_canary=True,
        canary_token="CANARY_FIN_KEY_3e4d5c6b",
        security_flag="CANARY_ACTIVE_HONEYPOT",
    ),
    FinancialAccount(
        account_id="acc_payroll_03",
        account_number="5544332211",
        iban="US12INTA0000005544332211",
        account_type=AccountType.CHECKING,
        balance=620400.00,
        currency="USD",
        holder_name="Apex Logistics Executive Payroll",
        is_canary=True,
        canary_token="CANARY_FIN_KEY_91a2b3c4",
        security_flag="CANARY_ACTIVE_HONEYPOT",
    ),
]


class FinancialSecurityLaboratory:
    """
    Controlled Financial Services Security Simulator.
    Interprets financial transaction payloads, detects fraud, and generates incident reports.
    """

    def __init__(self):
        self.accounts: Dict[str, FinancialAccount] = {a.account_id: a for a in SYNTHETIC_BANK_ACCOUNTS}
        self.incident_history: List[FinancialIncidentReport] = []
        self._seed_initial_incidents()

    def _seed_initial_incidents(self) -> None:
        """Seeds initial verified incident records for demonstration and investigation."""
        self.incident_history.append(
            FinancialIncidentReport(
                incident_id="fin_inc_91a0",
                timestamp=datetime.now(timezone.utc),
                attack_category="WIRE_THEFT",
                attacker_ip="185.220.101.5",
                targeted_account="acc_treasury_01",
                attempted_amount=2500000.00,
                detected_canary_tokens=["CANARY_FIN_KEY_7a8f9b2c"],
                risk_score=95,
                severity="CRITICAL",
                action_taken="TRANSACTION_INTERCEPTED_AND_QUARANTINED",
                evidence_chain=[
                    "Attempted unauthorized wire transfer of $2,500,000.00 to offshore SWIFT BIC 'CHASEUS33XXX'",
                    "Canary authorization token CANARY_FIN_KEY_7a8f9b2c observed in HTTP request header",
                    "Simulated Corporate Treasury balance drained - automatic deception alert fired",
                ],
            )
        )

    def list_accounts(self) -> List[FinancialAccount]:
        """Returns synthetic customer bank accounts."""
        return list(self.accounts.values())

    def list_incidents(self) -> List[FinancialIncidentReport]:
        """Returns forensic financial incident reports."""
        return list(self.incident_history)

    def process_transfer_attempt(
        self,
        request: FinancialTransferRequest,
        attacker_ip: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        """
        Evaluates a simulated wire transfer against deception and fraud detection rules.
        """
        now = datetime.now(timezone.utc)
        target_acc = self.accounts.get(request.source_account_id)

        evidence = []
        risk_score = 30
        is_fraud = False

        if target_acc and target_acc.is_canary:
            is_fraud = True
            risk_score += 45
            evidence.append(f"Target account '{request.source_account_id}' is a marked canary honeytoken resource.")

        if request.amount > 500000.0:
            is_fraud = True
            risk_score += 25
            evidence.append(f"High-value wire transfer threshold exceeded: ${request.amount:,.2f} requested.")

        if request.auth_token and "CANARY" in request.auth_token:
            is_fraud = True
            risk_score = 98
            evidence.append(f"Compromised canary credential presented: {request.auth_token}")

        risk_score = min(100, risk_score)
        severity = "CRITICAL" if risk_score >= 80 else ("HIGH" if risk_score >= 60 else "MEDIUM")

        incident_id = f"fin_inc_{hashlib.md5(f'{attacker_ip}:{request.amount}:{now.isoformat()}'.encode()).hexdigest()[:8]}"

        report = FinancialIncidentReport(
            incident_id=incident_id,
            timestamp=now,
            attack_category="WIRE_THEFT" if is_fraud else "LEGITIMATE_SIMULATION",
            attacker_ip=attacker_ip,
            targeted_account=request.source_account_id,
            attempted_amount=request.amount,
            detected_canary_tokens=[target_acc.canary_token] if target_acc else [],
            risk_score=risk_score,
            severity=severity,
            action_taken="TRANSACTION_FROZEN_AND_FLAGGED" if is_fraud else "TRANSACTION_APPROVED",
            evidence_chain=evidence or ["Standard transaction verification passed."],
        )

        if is_fraud:
            self.incident_history.insert(0, report)

        return {
            "status": "REJECTED_SECURITY_INTERVENTION" if is_fraud else "SUCCESS_PROCESSED",
            "message": "Transfer intercepted by Intent-Aware Deception fraud controller." if is_fraud else "Transfer completed.",
            "incident": report.model_dump(),
        }


# Global singleton
financial_security_lab = FinancialSecurityLaboratory()
