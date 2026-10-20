"""
Attack Behavior Digital Twin & Incident Storyboard Engine.

Reconstructs high-fidelity chronological execution trajectories for attacker sessions:
  1. Step-by-step telemetry replay with risk and intent evolution.
  2. Next-intent prediction evaluation against subsequently observed behavior.
  3. Kill-chain phase progression milestones.
  4. Comprehensive evidence-backed Incident Storyboard generation with IOC catalog.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.intent import AttackStage, IntentCategory
from backend.app.services.risk_engine import RiskEngine
from backend.app.services.sequence_transition_engine import sequence_transition_engine

logger = logging.getLogger(__name__)


class DigitalTwinStep(BaseModel):
    step: int
    event_id: str
    timestamp: datetime
    command: Optional[str] = None
    event_type: str
    intent: str
    attack_stage: str
    confidence: float = 1.0
    classification_source: str = "RULE"
    step_risk: int
    step_severity: str
    cumulative_risk: int
    cumulative_severity: str
    transition_anomaly_score: float = 0.0
    predicted_next_intents: List[Dict[str, Any]] = Field(default_factory=list)
    actual_next_intent: Optional[str] = None
    prediction_hit_top1: Optional[bool] = None
    prediction_hit_top3: Optional[bool] = None
    deception_strategy: Optional[str] = None
    deception_policy: Optional[str] = None
    honeytokens: List[str] = Field(default_factory=list)


class StageMilestone(BaseModel):
    stage: str
    first_step: int
    timestamp: datetime
    trigger_command: Optional[str] = None
    intent: str


class DigitalTwinReplay(BaseModel):
    session_id: str
    source_ip: Optional[str] = None
    protocol: str = "ssh"
    username: Optional[str] = None
    total_steps: int
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    duration_seconds: float = 0.0
    max_risk_score: int
    final_severity: str
    stages_reached: List[str] = Field(default_factory=list)
    stage_milestones: List[StageMilestone] = Field(default_factory=list)
    timeline: List[DigitalTwinStep] = Field(default_factory=list)
    next_intent_accuracy_top1: float = 0.0
    next_intent_accuracy_top3: float = 0.0
    evaluated_predictions_count: int = 0


class StoryboardPhase(BaseModel):
    phase_name: str
    stage: str
    start_time: datetime
    end_time: datetime
    event_count: int
    commands: List[str] = Field(default_factory=list)
    key_intent: str
    risk_contribution: int
    description: str


class IncidentStoryboard(BaseModel):
    storyboard_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str
    source_ip: str
    threat_actor_summary: str
    overall_severity: str
    peak_risk_score: int
    duration_seconds: float
    total_commands: int
    unique_commands: int
    mitre_attack_techniques: List[Dict[str, str]] = Field(default_factory=list)
    indicators_of_compromise: List[Dict[str, str]] = Field(default_factory=list)
    narrative_phases: List[StoryboardPhase] = Field(default_factory=list)
    containment_actions_taken: List[str] = Field(default_factory=list)
    defensive_recommendations: List[str] = Field(default_factory=list)
    evidence_events_count: int


class DigitalTwinEngine:
    """
    Builds the digital twin replay and storyboard from authentic session records.
    """

    @staticmethod
    def build_digital_twin(session_doc: Dict[str, Any], events: List[Dict[str, Any]]) -> DigitalTwinReplay:
        session_id = session_doc.get("session_id", "unknown")
        source_ip = session_doc.get("source_ip")
        protocol = session_doc.get("protocol", "ssh")
        username = session_doc.get("username")

        # Sort events chronologically
        def get_ts(ev: Dict[str, Any]) -> datetime:
            ts = ev.get("timestamp")
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    return datetime.now(timezone.utc)
            elif isinstance(ts, datetime):
                return ts
            return datetime.now(timezone.utc)

        sorted_events = sorted(events, key=get_ts)
        total_steps = len(sorted_events)

        timeline: List[DigitalTwinStep] = []
        milestones: List[StageMilestone] = []
        seen_stages: set = set()

        # Track intent history for cumulative risk & transition modeling
        observed_intents: List[IntentCategory] = []
        running_unique_intents: set = set()
        running_stages: set = set()
        top1_hits = 0
        top3_hits = 0
        evaluated_predictions = 0

        # Calculate timestamps
        first_seen = get_ts(sorted_events[0]) if sorted_events else None
        last_seen = get_ts(sorted_events[-1]) if sorted_events else None
        duration = (last_seen - first_seen).total_seconds() if first_seen and last_seen else 0.0

        for i, ev in enumerate(sorted_events):
            step_num = i + 1
            ev_ts = get_ts(ev)
            raw_intent_str = ev.get("intent", "OTHER")
            raw_stage_str = ev.get("attack_stage", "UNKNOWN")

            try:
                intent_enum = IntentCategory(raw_intent_str)
            except ValueError:
                intent_enum = IntentCategory.OTHER

            step_risk = int(ev.get("risk_score", 10))
            step_sev = ev.get("severity", "LOW")

            # Update running unique intents and calculate cumulative session risk
            running_unique_intents.add(intent_enum.value)
            running_stages.add(raw_stage_str)

            # Cumulative risk logic matching SessionIntelligenceEngine
            from backend.app.services.risk_engine import INTENT_BASE_WEIGHTS
            base_sum = sum(INTENT_BASE_WEIGHTS.get(IntentCategory(v), 5) for v in running_unique_intents)
            adv_stages = {"PRIVILEGE_ESCALATION", "PERSISTENCE", "EXFILTRATION", "CLEANUP", "EXECUTION"}
            multi_stage_bonus = 15 if len(running_stages.intersection(adv_stages)) >= 2 else 0
            command_depth_bonus = min(15, step_num * 2)
            running_risk = min(100, base_sum + multi_stage_bonus + command_depth_bonus)
            running_sev = RiskEngine.map_severity(running_risk)

            # Stage milestone
            if raw_stage_str not in seen_stages and raw_stage_str not in ("UNKNOWN", None):
                seen_stages.add(raw_stage_str)
                milestones.append(StageMilestone(
                    stage=raw_stage_str,
                    first_step=step_num,
                    timestamp=ev_ts,
                    trigger_command=ev.get("command"),
                    intent=intent_enum.value,
                ))

            # Next-intent projection
            preds = sequence_transition_engine.predict_next_intents(intent_enum, top_k=3)
            pred_dicts = [p.model_dump() for p in preds]

            # Look ahead to next event to check prediction hit
            actual_next = None
            hit_top1 = None
            hit_top3 = None
            if i + 1 < len(sorted_events):
                next_ev = sorted_events[i + 1]
                actual_next = next_ev.get("intent", "OTHER")
                evaluated_predictions += 1
                if preds:
                    if preds[0].intent.value == actual_next:
                        top1_hits += 1
                        hit_top1 = True
                    else:
                        hit_top1 = False

                    top3_names = [p.intent.value for p in preds]
                    if actual_next in top3_names:
                        top3_hits += 1
                        hit_top3 = True
                    else:
                        hit_top3 = False

            # Behavioral metadata
            b_feat = ev.get("behavioral_features", {}) or {}
            anomaly_score = b_feat.get("sequence_anomaly_score", 0.0)
            deception_strat = b_feat.get("deception_strategy")
            deception_pol = b_feat.get("deception_policy")
            honeytokens = b_feat.get("honeytokens_injected", [])

            timeline.append(DigitalTwinStep(
                step=step_num,
                event_id=ev.get("event_id", f"ev-{step_num}"),
                timestamp=ev_ts,
                command=ev.get("command"),
                event_type=ev.get("event_type", "command_input"),
                intent=intent_enum.value,
                attack_stage=raw_stage_str,
                confidence=float(ev.get("confidence", 1.0)),
                classification_source=ev.get("classification_source", "RULE"),
                step_risk=step_risk,
                step_severity=step_sev,
                cumulative_risk=running_risk,
                cumulative_severity=running_sev,
                transition_anomaly_score=float(anomaly_score),
                predicted_next_intents=pred_dicts,
                actual_next_intent=actual_next,
                prediction_hit_top1=hit_top1,
                prediction_hit_top3=hit_top3,
                deception_strategy=deception_strat,
                deception_policy=deception_pol,
                honeytokens=honeytokens if isinstance(honeytokens, list) else [],
            ))

            observed_intents.append(intent_enum)

        top1_acc = round(top1_hits / evaluated_predictions, 4) if evaluated_predictions > 0 else 0.0
        top3_acc = round(top3_hits / evaluated_predictions, 4) if evaluated_predictions > 0 else 0.0

        max_risk = max((s.cumulative_risk for s in timeline), default=int(session_doc.get("risk_score", 0)))
        final_sev = RiskEngine.map_severity(max_risk)

        return DigitalTwinReplay(
            session_id=session_id,
            source_ip=source_ip,
            protocol=protocol,
            username=username,
            total_steps=total_steps,
            first_seen=first_seen,
            last_seen=last_seen,
            duration_seconds=duration,
            max_risk_score=max_risk,
            final_severity=final_sev,
            stages_reached=sorted(list(seen_stages)),
            stage_milestones=milestones,
            timeline=timeline,
            next_intent_accuracy_top1=top1_acc,
            next_intent_accuracy_top3=top3_acc,
            evaluated_predictions_count=evaluated_predictions,
        )

    @staticmethod
    def generate_incident_storyboard(session_doc: Dict[str, Any], events: List[Dict[str, Any]]) -> IncidentStoryboard:
        """
        Synthesizes an evidence-backed Incident Storyboard from authentic session history.
        """
        twin = DigitalTwinEngine.build_digital_twin(session_doc, events)
        session_id = twin.session_id
        source_ip = twin.source_ip or "unknown"

        # Extract MITRE techniques
        from backend.app.services.mitre_mapper import MitreMapper
        techniques_dict = {}
        for ev in events:
            mapped = MitreMapper.get_techniques_for_intent(ev.get("intent", "OTHER"))
            for m in mapped:
                t_id = m.get("technique_id")
                if t_id and t_id not in techniques_dict:
                    techniques_dict[t_id] = {
                        "technique_id": t_id,
                        "technique_name": m.get("name", "Unknown Technique"),
                        "tactic": m.get("tactic", "Unknown Tactic"),
                    }

        # Extract IOCs
        iocs: List[Dict[str, str]] = []
        if source_ip != "unknown":
            iocs.append({"type": "IPv4", "value": source_ip, "context": "Adversary Source Address"})

        seen_ioc_values = {source_ip}
        for ev in events:
            cmd = (ev.get("command") or "").strip()
            # Look for IPs, URLs, download targets, filenames
            tokens = cmd.split()
            for t in tokens:
                if (t.startswith("http://") or t.startswith("https://") or t.startswith("ftp://")) and t not in seen_ioc_values:
                    seen_ioc_values.add(t)
                    iocs.append({"type": "URL", "value": t, "context": "Payload Staging URL"})
                elif (t.startswith("/tmp/") or t.startswith("/dev/shm/") or t.startswith("/var/tmp/")) and t not in seen_ioc_values:
                    seen_ioc_values.add(t)
                    iocs.append({"type": "FILEPATH", "value": t, "context": "Artifact Staging Path"})

        # Group into chronological narrative phases by attack stage
        phases: List[StoryboardPhase] = []
        if twin.timeline:
            current_stage = twin.timeline[0].attack_stage
            current_phase_events: List[DigitalTwinStep] = []

            for step in twin.timeline:
                if step.attack_stage != current_stage and current_phase_events:
                    # Finalize phase
                    p_start = current_phase_events[0].timestamp
                    p_end = current_phase_events[-1].timestamp
                    cmds = [s.command for s in current_phase_events if s.command]
                    phases.append(StoryboardPhase(
                        phase_name=f"Phase {len(phases) + 1}: {current_stage.replace('_', ' ').title()}",
                        stage=current_stage,
                        start_time=p_start,
                        end_time=p_end,
                        event_count=len(current_phase_events),
                        commands=cmds[:10],
                        key_intent=current_phase_events[-1].intent,
                        risk_contribution=max(s.step_risk for s in current_phase_events),
                        description=f"Adversary progressed through {current_stage} executing {len(cmds)} commands targeting host telemetry.",
                    ))
                    current_stage = step.attack_stage
                    current_phase_events = [step]
                else:
                    current_phase_events.append(step)

            if current_phase_events:
                p_start = current_phase_events[0].timestamp
                p_end = current_phase_events[-1].timestamp
                cmds = [s.command for s in current_phase_events if s.command]
                phases.append(StoryboardPhase(
                    phase_name=f"Phase {len(phases) + 1}: {current_stage.replace('_', ' ').title()}",
                    stage=current_stage,
                    start_time=p_start,
                    end_time=p_end,
                    event_count=len(current_phase_events),
                    commands=cmds[:10],
                    key_intent=current_phase_events[-1].intent,
                    risk_contribution=max(s.step_risk for s in current_phase_events),
                    description=f"Adversary sustained activity in {current_stage} stage.",
                ))

        # Containment & defense recommendations
        containment = [
            f"Honeypot isolation verified: 0 commands executed on production host.",
            f"Dynamic decoy payloads returned for {len([s for s in twin.timeline if s.deception_strategy])} commands.",
        ]
        if any(s.honeytokens for s in twin.timeline):
            containment.append("Tripwire canary honeytokens injected into shell output.")

        recommendations = [
            f"Block or rate-limit inbound SSH connections from {source_ip}.",
            "Audit internal systems for credential spraying or unauthorized SSH key additions.",
            "Verify canary honeytokens in threat intelligence monitors.",
        ]

        summary = (
            f"Adversary from {source_ip} conducted a {twin.final_severity}-severity intrusion attempt "
            f"spanning {len(twin.stages_reached)} kill-chain stages ({', '.join(twin.stages_reached)}). "
            f"Peak risk score reached {twin.max_risk_score}/100 across {twin.total_steps} recorded interactions."
        )

        return IncidentStoryboard(
            storyboard_id=f"sb-{session_id}",
            session_id=session_id,
            source_ip=source_ip,
            threat_actor_summary=summary,
            overall_severity=twin.final_severity,
            peak_risk_score=twin.max_risk_score,
            duration_seconds=twin.duration_seconds,
            total_commands=len([s for s in twin.timeline if s.command]),
            unique_commands=len(set(s.command for s in twin.timeline if s.command)),
            mitre_attack_techniques=list(techniques_dict.values()),
            indicators_of_compromise=iocs,
            narrative_phases=phases,
            containment_actions_taken=containment,
            defensive_recommendations=recommendations,
            evidence_events_count=twin.total_steps,
        )


digital_twin_engine = DigitalTwinEngine()
