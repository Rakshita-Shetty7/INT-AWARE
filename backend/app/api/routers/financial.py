"""
Financial Services Security Laboratory REST Router.

Provides endpoints for synthetic banking decoys, fraud detection, and forensic incident reporting.
"""

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.research.financial_lab.models import (
    FinancialAccount,
    FinancialIncidentReport,
    FinancialTransferRequest,
)
from backend.app.research.financial_lab.service import financial_security_lab

router = APIRouter(prefix="/financial", tags=["Financial Services Security Lab"])


class TransferSimulationPayload(BaseModel):
    source_account_id: str = Field(..., description="e.g., acc_treasury_01")
    destination_iban: str = Field(..., description="Offshore or external IBAN")
    destination_swift_bic: str = Field("CHASEUS33XXX", description="Target SWIFT code")
    amount: float = Field(..., ge=1.0)
    auth_token: str = Field("CANARY_FIN_KEY_7a8f9b2c", description="Authorization bearer token")
    attacker_ip: str = Field("185.220.101.5", description="Attacker IP address")


@router.get("/accounts", response_model=List[FinancialAccount], summary="List Synthetic Bank Decoy Accounts")
def get_accounts() -> List[FinancialAccount]:
    """
    Returns synthetic banking accounts with canary financial tokens.
    """
    return financial_security_lab.list_accounts()


@router.get("/incidents", response_model=List[FinancialIncidentReport], summary="List Financial Incident Reports")
def get_incidents() -> List[FinancialIncidentReport]:
    """
    Returns forensic reports of detected wire diversion and financial fraud attempts.
    """
    return financial_security_lab.list_incidents()


@router.post("/transfer", summary="Submit Simulated Wire Transfer")
def submit_transfer(req: TransferSimulationPayload) -> Dict[str, Any]:
    """
    Evaluates a simulated wire transfer against fraud rules and canary token traps.
    """
    transfer_req = FinancialTransferRequest(
        source_account_id=req.source_account_id,
        destination_iban=req.destination_iban,
        destination_swift_bic=req.destination_swift_bic,
        amount=req.amount,
        auth_token=req.auth_token,
    )
    return financial_security_lab.process_transfer_attempt(
        request=transfer_req,
        attacker_ip=req.attacker_ip,
    )
