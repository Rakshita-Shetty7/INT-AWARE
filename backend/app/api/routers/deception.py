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


