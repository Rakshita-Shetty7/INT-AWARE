"""
Financial Services Security Laboratory Models.

Defines schemas for synthetic core banking decoys, customer accounts,
wire transfers, canary financial tokens, and fraud incident forensics.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AccountType(str, Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    CORPORATE_TREASURY = "CORPORATE_TREASURY"
    ESCROW = "ESCROW"


class FinancialAccount(BaseModel):
    """Synthetic customer bank account decoy."""
    account_id: str
    account_number: str
    iban: str
    account_type: AccountType
    balance: float
    currency: str = "USD"
    holder_name: str
    is_canary: bool = True
    canary_token: str
    security_flag: str = "DECOY_MONITORED"


class FinancialTransferRequest(BaseModel):
    """Wire or payment transfer payload submitted to simulated banking API."""
    source_account_id: str
    destination_iban: str
    destination_swift_bic: str
    amount: float = Field(..., ge=0.01)
    currency: str = "USD"
    memo: Optional[str] = "Corporate supplier payout"
    auth_token: Optional[str] = None


class FinancialIncidentReport(BaseModel):
    """Forensic report documenting suspicious financial service interactions."""
    incident_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attack_category: str = Field(..., description="CREDENTIAL_STUFFING, WIRE_THEFT, API_TAMPERING, or PRIVILEGE_ABUSE")
    attacker_ip: str
    targeted_account: Optional[str] = None
    attempted_amount: float = 0.0
    detected_canary_tokens: List[str] = Field(default_factory=list)
    risk_score: int = Field(..., ge=0, le=100)
    severity: str = Field("HIGH")
    action_taken: str = Field("TRANSACTION_FROZEN_AND_FLAGGED")
    evidence_chain: List[str] = Field(default_factory=list)
