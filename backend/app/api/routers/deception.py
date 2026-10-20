"""
Deception & Sequence Intelligence REST router.

Provides endpoints for adaptive deception policies, dynamic honeytoken inspection,
safe response simulation, and Markov sequence transition matrices.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from backend.app.models.intent import AttackStage, IntentCategory
from backend.app.services.adaptive_deception_engine import (
    AdaptiveDeceptionEngine,
    DeceptionDecision,
    adaptive_deception_engine,
)
from backend.app.services.beelzebub_fleet import (
    DecoyService,
    Honeytoken,
    beelzebub_fleet_manager,
)
from backend.app.services.caronte_analyst import (
    CaronteInvestigationReport,
    caronte_analyst_engine,
)
from backend.app.services.sequence_transition_engine import (
    EMPIRICAL_TRANSITION_PRIORS,
    NextIntentPrediction,
    SequenceTransitionAnalysis,
    sequence_transition_engine,
)

router = APIRouter(prefix="/deception", tags=["Deception & Sequence Intelligence"])


class SimulationRequest(BaseModel):
    command: str = Field(..., description="Simulated command string to test deception response for")
    intent: IntentCategory = Field(IntentCategory.RECONNAISSANCE, description="Attacker intent category")
    attack_stage: AttackStage = Field(AttackStage.RECONNAISSANCE, description="Current attack stage")
    session_id: str = Field("sim-session-01", description="Session identifier")
    risk_score: int = Field(25, ge=0, le=100, description="Session risk score")


class TransitionCheckRequest(BaseModel):
    current_intent: IntentCategory
    intent_history: List[IntentCategory] = Field(default_factory=list)
    inter_command_delays: Optional[List[float]] = None


@router.get("/policies", summary="List Active Cyber Deception Policies")
def get_deception_policies() -> List[Dict[str, Any]]:
    """
    Returns configured adaptive deception policies, decoy types, and safety constraints.
    """
    return [
        {
            "policy_id": "POL_RECON_EMULATION",
            "intent_trigger": "RECONNAISSANCE",
            "strategy": "SIMULATED_SUCCESS",
            "description": "Returns plausible Linux debian architecture metadata, open ports, and system info.",
            "safety_model": "Zero host execution - strictly sandboxed template synthesis",
            "tar_pit_enabled": False,
        },
        {
            "policy_id": "POL_HONEYTOKEN_CRED_INJECTION",
            "intent_trigger": "CREDENTIAL_ACCESS",
            "strategy": "HONEYTOKEN_INJECTION",
            "description": "Injects synthetic bcrypt/shadow hashes, fake SSH keys, and canary AWS tokens.",
            "safety_model": "Zero host execution - deterministic canary token generator",
            "tar_pit_enabled": False,
        },
        {
            "policy_id": "POL_DECOY_DISCOVERY",
            "intent_trigger": "DISCOVERY",
            "strategy": "DECOY_ARTIFACT",
            "description": "Returns simulated file trees with alluring backup files and canary database credentials.",
            "safety_model": "Zero host execution - static virtual file tree",
            "tar_pit_enabled": False,
        },
        {
            "policy_id": "POL_TARPIT_THROTTLE",
            "intent_trigger": "EXECUTION / EXPLOITATION",
            "strategy": "TARPIT_DELAY",
            "description": "Applies proportional response delay (200-800ms) to exhaust automated scanner threads.",
            "safety_model": "Zero host execution - delayed status 0 acknowledgement",
            "tar_pit_enabled": True,
        },
        {
            "policy_id": "POL_DEFAULT_SANDBOX",
            "intent_trigger": "OTHER",
            "strategy": "SIMULATED_SUCCESS",
            "description": "Default isolated sandbox prompt acknowledgement.",
            "safety_model": "Zero host execution - empty response",
            "tar_pit_enabled": False,
        },
    ]


@router.post("/simulate", response_model=DeceptionDecision, summary="Simulate Safe Deception Response")
def simulate_deception(req: SimulationRequest) -> DeceptionDecision:
    """
    Evaluates what simulated response, canary honeytokens, and tar-pit delay the engine
    would present to an attacker for a given command and intent. Zero host execution.
    """
    return adaptive_deception_engine.select_deception_response(
        command=req.command,
        intent=req.intent,
        attack_stage=req.attack_stage,
        session_id=req.session_id,
        risk_score=req.risk_score,
    )


@router.get("/transitions/matrix", summary="Get Empirical Markov Transition Matrix")
def get_transition_matrix() -> Dict[str, Dict[str, float]]:
    """
    Returns empirical transition likelihoods P(Intent_t | Intent_{t-1}) across all 10 intent classes.
    """
    return EMPIRICAL_TRANSITION_PRIORS


@router.post("/transitions/evaluate", response_model=SequenceTransitionAnalysis, summary="Evaluate Sequence Transition")
def evaluate_sequence_transition(req: TransitionCheckRequest) -> SequenceTransitionAnalysis:
    """
    Calculates transition likelihood, sequence anomaly score, and next-intent projections.
    """
    return sequence_transition_engine.evaluate_transition(
        current_intent=req.current_intent,
        intent_history=req.intent_history,
        inter_command_delays=req.inter_command_delays,
    )


# ---------------------------------------------------------------------------
# Beelzebub Fleet Management & Honeytoken Registry
# ---------------------------------------------------------------------------

class CaronteInvestigationRequest(BaseModel):
    session_id: str = Field("sess-live-probe", description="Session identifier")
    source_ip: str = Field("198.51.100.42", description="Attacker source IP")
    commands: List[str] = Field(default_factory=list, description="Sequence of attacker commands executed")
    intents: Optional[List[IntentCategory]] = None


@router.get("/fleet/summary", summary="Get Beelzebub Fleet Infrastructure Summary")
def get_fleet_summary() -> Dict[str, Any]:
    """
    Returns deployment metrics, protocol distribution, and honeytoken statistics across the decoy fleet.
    """
    return beelzebub_fleet_manager.get_fleet_summary()


@router.get("/decoys", response_model=List[DecoyService], summary="List All Active Beelzebub Decoy Services")
def list_decoys() -> List[DecoyService]:
    """
    Returns all configured low-code decoys across SSH, HTTP, TCP, Telnet, and MCP AI agent traps.
    """
    return beelzebub_fleet_manager.list_decoys()


@router.get("/decoys/{decoy_id}", response_model=DecoyService, summary="Get Specific Decoy Service & YAML Config")
def get_decoy(decoy_id: str) -> DecoyService:
    decoy = beelzebub_fleet_manager.get_decoy(decoy_id)
    if not decoy:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Decoy service {decoy_id} not found")
    return decoy


@router.get("/honeytokens", response_model=List[Honeytoken], summary="List Honeytoken Traps & Canary Credentials")
def list_honeytokens() -> List[Honeytoken]:
    """
    Returns deployed canary credentials (AWS keys, shadow hashes, DB URIs, RAG tokens) and tripwire states.
    """
    return beelzebub_fleet_manager.list_honeytokens()


@router.post("/honeytokens/{token_id}/trip", response_model=Honeytoken, summary="Manually Trigger / Test Honeytoken Tripwire")
def trip_honeytoken(token_id: str) -> Honeytoken:
    tok = beelzebub_fleet_manager.record_token_trip(token_id)
    if not tok:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Honeytoken {token_id} not found")
    return tok


@router.post("/caronte/investigate", response_model=CaronteInvestigationReport, summary="Execute Caronte AI Threat Investigation")
def run_caronte_investigation(req: CaronteInvestigationRequest) -> CaronteInvestigationReport:
    """
    Autonomous forensic analysis of an attacker session: MITRE ATT&CK mapping, IOC extraction,
    attacker sophistication rating, and deception containment dossier.
    """
    return caronte_analyst_engine.investigate(
        session_id=req.session_id,
        source_ip=req.source_ip,
        commands=req.commands,
        intents=req.intents,
    )


# ---------------------------------------------------------------------------
# Deception Effectiveness Laboratory Endpoints
# ---------------------------------------------------------------------------

class LabExperimentRequest(BaseModel):
    commands: List[str] = Field(default_factory=list, description="Sequence of shell commands to test")
    session_id: str = Field("exp-session-live", description="Session identifier")


@router.get("/lab/benchmark", summary="Get Standard Deception Effectiveness Benchmark")
def get_lab_benchmark() -> Dict[str, Any]:
    """
    Runs an empirical benchmark comparing static honeypot responses against adaptive intent-aware deception.
    """
    from backend.app.services.deception_lab import deception_effectiveness_lab
    report = deception_effectiveness_lab.run_replay_experiment(commands=[])
    return report.model_dump()


@router.post("/lab/replay-experiment", summary="Run Custom Deception Replay Experiment")
def run_lab_experiment(req: LabExperimentRequest) -> Dict[str, Any]:
    """
    Executes controlled comparative replay with custom commands to measure dwell time,
    command capture gains, and tar-pit evasion resistance.
    """
    from backend.app.services.deception_lab import deception_effectiveness_lab
    report = deception_effectiveness_lab.run_replay_experiment(commands=req.commands, session_id=req.session_id)
    return report.model_dump()


