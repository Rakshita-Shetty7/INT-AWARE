"""
AI Services & Agent Security Laboratory Models.

Defines schemas for prompt injection evaluation, simulated MCP tool call monitoring,
and synthetic RAG honeytoken document leakage detection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PromptAttackType(str, Enum):
    JAILBREAK = "JAILBREAK"
    SYSTEM_PROMPT_EXTRACTION = "SYSTEM_PROMPT_EXTRACTION"
    INSTRUCTION_OVERRIDE = "INSTRUCTION_OVERRIDE"
    ROLEPLAY_DEFLECTION = "ROLEPLAY_DEFLECTION"
    ADVERSARIAL_SUFFIX = "ADVERSARIAL_SUFFIX"


class PromptEvaluationResult(BaseModel):
    """Result of evaluating a prompt string for injection or jailbreak attempts."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    prompt_snippet: str
    is_injection_detected: bool
    attack_category: Optional[PromptAttackType] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_score: int = Field(..., ge=0, le=100)
    severity: str = Field("LOW")
    detected_patterns: List[str] = Field(default_factory=list)
    mitigation_action: str = Field("ALLOW", description="ALLOW, SANITIZE, or BLOCK_WITH_DECEPTION")
    deception_prompt_response: Optional[str] = None


class MCPToolCall(BaseModel):
    """Simulated Model Context Protocol (MCP) tool invocation payload."""
    tool_name: str = Field(..., description="e.g., execute_sql, read_internal_file, dispatch_http_request")
    arguments: Dict[str, Any] = Field(default_factory=dict)
    caller_agent_id: str = "agent-autonomous-worker-01"
    session_id: str = "ai_sess_01"


class MCPToolSecurityEvaluation(BaseModel):
    """Security assessment of an agent's MCP tool execution request."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_name: str
    is_authorized: bool
    is_suspicious_parameter: bool
    risk_score: int = Field(..., ge=0, le=100)
    action: str = Field("ALLOW", description="ALLOW, QUARANTINE, or MOCK_WITH_DECOY")
    evidence: List[str] = Field(default_factory=list)
    simulated_decoy_output: Optional[str] = None


class RAGCanaryDocument(BaseModel):
    """Synthetic confidential document loaded into retrieval vector store with canary tokens."""
    doc_id: str
    title: str
    classification_level: str = "TOP_SECRET_CANARY"
    canary_token: str
    content_snippet: str
    leak_alert_policy: str = "IMMEDIATE_SOC_INCIDENT"
