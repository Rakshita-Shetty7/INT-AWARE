"""
Research Modules REST Router: Industrial AI Robustness & Vulnerability Verification Laboratories.

Exposes separate research extension laboratories without modifying the core INT-AWARE platform.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from backend.app.api.dependencies import get_persistence_service
from backend.app.services.persistence_service import PersistenceService

from backend.app.research.industrial_lab.anomaly_detector import (
    SWAT_PHYSICAL_INVARIANTS,
    AdversarialPerturbationTestResult,
    ICSAnomalyDetectionResult,
    SensorInvariant,
    industrial_anomaly_detector,
)
from backend.app.research.vuln_lab.vulnerability_verifier import (
    CURATED_CVE_BENCHMARKS,
    VerifiedCVEBenchmark,
    VulnerabilityVerificationResult,
    vulnerability_verification_lab,
)

router = APIRouter(prefix="/research", tags=["Research Laboratories"])


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class IndustrialSensorTelemetryRequest(BaseModel):
    telemetry: Dict[str, float] = Field(
        ...,
        description="Sensor measurements mapping tag to value, e.g. {'FIT101': 2.4, 'LIT101': 850.0}",
    )


class AdversarialTestRequest(BaseModel):
    dataset_name: str = Field("SWaT", description="ICS Dataset: SWaT, WADI, or HAI")
    attack_type: str = Field("SPOOFING", description="Attack modality: SPOOFING, SCALING, or FREEZE")
    epsilon_bound: float = Field(0.15, ge=0.01, le=1.0, description="L-infinity perturbation magnitude bound")
    num_samples: int = Field(50, ge=10, le=500, description="Number of simulation steps")


class ExploitVerificationRequest(BaseModel):
    payload: str = Field(..., description="Exploit or shell payload to verify in safe sandbox")
    target_cve: Optional[str] = Field(None, description="Optional target CVE to evaluate against")


# ---------------------------------------------------------------------------
# Industrial AI Robustness Endpoints
# ---------------------------------------------------------------------------

@router.get("/industrial/invariants", response_model=List[SensorInvariant], summary="List Industrial Sensor Invariants")
def get_sensor_invariants() -> List[SensorInvariant]:
    """
    Returns verified physical invariants (min/max bounds, max rates of change) for SWaT ICS sensors.
    """
    return list(industrial_anomaly_detector.invariants.values())


@router.post("/industrial/evaluate", response_model=ICSAnomalyDetectionResult, summary="Evaluate Industrial Sensor Telemetry")
def evaluate_sensor_telemetry(req: IndustrialSensorTelemetryRequest) -> ICSAnomalyDetectionResult:
    """
    Evaluates real-time industrial time-series sensor measurements against physical process invariants.
    """
    return industrial_anomaly_detector.analyze_sensor_reading(req.telemetry)


@router.post("/industrial/adversarial-test", response_model=AdversarialPerturbationTestResult, summary="Run Adversarial Perturbation Benchmark")
def run_adversarial_test(req: AdversarialTestRequest) -> AdversarialPerturbationTestResult:
    """
    Simulates bounded adversarial sensor noise injection to assess model robustness degradation.
    """
    return industrial_anomaly_detector.evaluate_adversarial_robustness(
        dataset_name=req.dataset_name,
        attack_type=req.attack_type,
        epsilon_bound=req.epsilon_bound,
        num_samples=req.num_samples,
    )


# ---------------------------------------------------------------------------
# Vulnerability Verification Laboratory Endpoints
# ---------------------------------------------------------------------------

@router.get("/vuln/benchmarks", response_model=List[VerifiedCVEBenchmark], summary="List Curated Vulnerability Benchmarks")
def get_vulnerability_benchmarks() -> List[VerifiedCVEBenchmark]:
    """
    Returns curated CVE exploit benchmarks (Log4Shell, regreSSHion, Spring4Shell, Shellshock, Redis).
    """
    return vulnerability_verification_lab.list_benchmarks()


@router.post("/vuln/verify", response_model=VulnerabilityVerificationResult, summary="Verify Exploit Payload in Safe Sandbox")
def verify_exploit_payload(req: ExploitVerificationRequest) -> VulnerabilityVerificationResult:
    """
    Safely evaluates an exploit payload in an in-memory sandbox and determines detection
    confidence, intent classification, and adaptive deception response with zero host execution.
    """
    return vulnerability_verification_lab.verify_payload(
        payload=req.payload,
        target_cve=req.target_cve,
    )


# ---------------------------------------------------------------------------
# Evidence-First AI Copilot Endpoints
# ---------------------------------------------------------------------------

class CopilotQueryRequest(BaseModel):
    query: str = Field(..., description="Investigation prompt or question")
    session_id: Optional[str] = Field(None, description="Optional target session context")
    source_ip: Optional[str] = Field(None, description="Optional target IP context")


@router.post("/copilot/query", summary="Query Evidence-First AI Security Copilot")
def query_copilot(
    req: CopilotQueryRequest,
    persistence: PersistenceService = Depends(get_persistence_service)
) -> Dict[str, Any]:
    """
    Answers investigation queries strictly grounded in authentic honeypot telemetry.
    Explicitly separates verified facts (with event_id citations) from hypotheses and uncertainties.
    """
    from backend.app.services.copilot_engine import copilot_engine
    res = copilot_engine.query(
        question=req.query,
        session_id=req.session_id,
        source_ip=req.source_ip,
        persistence_override=persistence,
    )
    return res.model_dump()

