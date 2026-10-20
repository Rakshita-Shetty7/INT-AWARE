"""
AI Services & Agent Security Laboratory REST Router.

Provides endpoints for evaluating prompt injections, inspecting simulated MCP tool calls,
and testing RAG honeytoken document leakage.
"""

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.research.ai_lab.models import (
    MCPToolCall,
    MCPToolSecurityEvaluation,
    PromptEvaluationResult,
    RAGCanaryDocument,
)
from backend.app.research.ai_lab.service import ai_security_lab

router = APIRouter(prefix="/ai-security", tags=["AI Services Security Lab"])


class PromptTestRequest(BaseModel):
    prompt: str = Field(..., description="Prompt string to scan for jailbreak/injection patterns")


class RAGTestRequest(BaseModel):
    query: str = Field(..., description="Query to test against synthetic RAG vector knowledge base")


@router.post("/evaluate-prompt", response_model=PromptEvaluationResult, summary="Evaluate Prompt Injection & Jailbreak")
def evaluate_prompt(req: PromptTestRequest) -> PromptEvaluationResult:
    """
    Scans a prompt string for instruction overrides, jailbreaks, and system prompt exfiltration.
    """
    return ai_security_lab.evaluate_prompt(req.prompt)


@router.post("/evaluate-tool-call", response_model=MCPToolSecurityEvaluation, summary="Inspect Agent MCP Tool Call")
def evaluate_tool_call(tool_call: MCPToolCall) -> MCPToolSecurityEvaluation:
    """
    Monitors a simulated Model Context Protocol (MCP) tool call for privilege escalation and parameter injection.
    """
    return ai_security_lab.evaluate_mcp_tool_call(tool_call)


@router.get("/rag-canaries", response_model=List[RAGCanaryDocument], summary="List Synthetic RAG Canary Documents")
def get_rag_canary_documents() -> List[RAGCanaryDocument]:
    """
    Returns synthetic documents containing trackable canary honeytoken strings.
    """
    return ai_security_lab.list_canary_documents()


@router.post("/test-rag-leak", summary="Test RAG Knowledge Retrieval Leakage")
def test_rag_leak(req: RAGTestRequest) -> Dict[str, Any]:
    """
    Tests whether a query extracts canary honeytokens from restricted synthetic RAG documents.
    """
    return ai_security_lab.test_rag_leakage(req.query)
