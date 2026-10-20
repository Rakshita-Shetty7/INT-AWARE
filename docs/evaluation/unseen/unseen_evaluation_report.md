# Phase 10 - Unseen / Ambiguous Behaviour Evaluation Report
## Intent-Aware Deception System v1.0 RC (FROZEN)

> **Evaluation Date**: 2026-08-19T18:33:25.573812+00:00  
> **Production code**: NOT MODIFIED.  
> **Gemini API Available**: YES

---

## Objective

Phase 9 evaluated 42 cases derived directly from rule signatures, achieving
perfect scores (Accuracy=1.0). Phase 10 evaluates the same frozen classifier
on **28 cases designed to NOT match existing rule patterns**, to test whether
the Gemini layer provides measurable value on novel and ambiguous behaviour.

## Case Type Taxonomy

| Type | Description | Count |
| :--- | :--- | ---: |
| A | No rule match -> rule=OTHER(0.30) -> Gemini primary | 24 |
| B | Partial rule match (conf <0.90) -> Gemini consulted | 1 |
| C | Rule matches WRONG intent -> tests Gemini correction | 1 |
| D | Control/benign (should remain OTHER) | 2 |

---

## Task 3 - Gemini Usage

| Metric | Value |
| :--- | ---: |
| Total cases | 28 |
| Rule-only resolved (Gemini not attempted) | 0 |
| Gemini attempted | 28 (100.0%) |
| Gemini succeeded (source=GEMINI/HYBRID) | 0 |
| Gemini FALLBACK (attempted, failed) | 28 |
| Changed predictions | 0 |

---

## Task 4 - Classification Metrics

> **Statistical note**: 28 cases is illustrative. Metrics are not statistically significant
> for production-level performance claims.

| Metric | Rule-Only | Hybrid | Delta |
| :--- | ---: | ---: | ---: |
| Accuracy | 0.1071 | 0.1071 | 0.0000 |
| Macro Precision | 0.1208 | 0.1208 | 0.0000 |
| Macro Recall | 0.1667 | 0.1667 | 0.0000 |
| Macro F1 | 0.0919 | 0.0919 | 0.0000 |
| Weighted F1 | 0.0590 | 0.0590 | 0.0000 |

### Per-Class Comparison

| Intent | Support | Rule P | Rule R | Rule F1 | Hybrid P | Hybrid R | Hybrid F1 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CLEANUP | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| CREDENTIAL_ACCESS | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| DISCOVERY | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| EXECUTION | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| EXFILTRATION | 2 | 1.0000 | 0.5000 | 0.6667 | 1.0000 | 0.5000 | 0.6667 |
| OTHER | 2 | 0.0870 | 1.0000 | 0.1600 | 0.0870 | 1.0000 | 0.1600 |
| PERSISTENCE | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| PRIVILEGE_ESCALATION | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| RECONNAISSANCE | 4 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

---

## Task 5 - Hybrid Value Analysis

All cases where Gemini was attempted (source != RULE):

| Test ID | Expected | Rule Output | Hybrid Output | Source | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC-U-CRED-01 | CREDENTIAL_ACCESS | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-CRED-02 | CREDENTIAL_ACCESS | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-CRED-03 | CREDENTIAL_ACCESS | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-CRED-04 | CREDENTIAL_ACCESS | DISCOVERY | DISCOVERY | FALLBACK | **UNCHANGED** |
| TC-U-RECON-01 | RECONNAISSANCE | DISCOVERY | DISCOVERY | FALLBACK | **UNCHANGED** |
| TC-U-RECON-02 | RECONNAISSANCE | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-RECON-03 | RECONNAISSANCE | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-RECON-04 | RECONNAISSANCE | DISCOVERY | DISCOVERY | FALLBACK | **UNCHANGED** |
| TC-U-DISC-01 | DISCOVERY | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-DISC-02 | DISCOVERY | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-DISC-03 | DISCOVERY | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-DISC-04 | DISCOVERY | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-EXEC-01 | EXECUTION | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-EXEC-02 | EXECUTION | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-EXEC-03 | EXECUTION | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-PRIV-01 | PRIVILEGE_ESCALATION | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-PRIV-02 | PRIVILEGE_ESCALATION | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-PRIV-03 | PRIVILEGE_ESCALATION | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-PERS-01 | PERSISTENCE | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-PERS-02 | PERSISTENCE | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-PERS-03 | PERSISTENCE | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-EXFIL-01 | EXFILTRATION | EXFILTRATION | EXFILTRATION | FALLBACK | **UNCHANGED** |
| TC-U-EXFIL-02 | EXFILTRATION | EXECUTION | EXECUTION | FALLBACK | **UNCHANGED** |
| TC-U-CLEAN-01 | CLEANUP | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-CLEAN-02 | CLEANUP | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-CLEAN-03 | CLEANUP | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-OTHER-01 | OTHER | OTHER | OTHER | FALLBACK | **UNCHANGED** |
| TC-U-OTHER-02 | OTHER | OTHER | OTHER | FALLBACK | **UNCHANGED** |

---

## Task 6 - False Positive / False Negative Analysis

| Test ID | Expected | Predicted | Rule Output | Source | Analysis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC-U-CRED-01 | CREDENTIAL_ACCESS | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'CREDENTIAL_AC |
| TC-U-CRED-02 | CREDENTIAL_ACCESS | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'CREDENTIAL_AC |
| TC-U-CRED-03 | CREDENTIAL_ACCESS | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'CREDENTIAL_AC |
| TC-U-CRED-04 | CREDENTIAL_ACCESS | DISCOVERY | DISCOVERY | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'DISCOVERY'. With working Gemini, 'CREDENTIA |
| TC-U-RECON-01 | RECONNAISSANCE | DISCOVERY | DISCOVERY | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'DISCOVERY'. With working Gemini, 'RECONNAIS |
| TC-U-RECON-02 | RECONNAISSANCE | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'RECONNAISSANC |
| TC-U-RECON-03 | RECONNAISSANCE | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'RECONNAISSANC |
| TC-U-RECON-04 | RECONNAISSANCE | DISCOVERY | DISCOVERY | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'DISCOVERY'. With working Gemini, 'RECONNAIS |
| TC-U-DISC-01 | DISCOVERY | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'DISCOVERY' wo |
| TC-U-DISC-02 | DISCOVERY | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'DISCOVERY' wo |
| TC-U-DISC-03 | DISCOVERY | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'DISCOVERY' wo |
| TC-U-DISC-04 | DISCOVERY | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'DISCOVERY' wo |
| TC-U-EXEC-01 | EXECUTION | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'EXECUTION' wo |
| TC-U-EXEC-02 | EXECUTION | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'EXECUTION' wo |
| TC-U-EXEC-03 | EXECUTION | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'EXECUTION' wo |
| TC-U-PRIV-01 | PRIVILEGE_ESCALATION | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'PRIVILEGE_ESC |
| TC-U-PRIV-02 | PRIVILEGE_ESCALATION | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'PRIVILEGE_ESC |
| TC-U-PRIV-03 | PRIVILEGE_ESCALATION | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'PRIVILEGE_ESC |
| TC-U-PERS-01 | PERSISTENCE | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'PERSISTENCE'  |
| TC-U-PERS-02 | PERSISTENCE | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'PERSISTENCE'  |
| TC-U-PERS-03 | PERSISTENCE | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'PERSISTENCE'  |
| TC-U-EXFIL-02 | EXFILTRATION | EXECUTION | EXECUTION | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'EXECUTION'. With working Gemini, 'EXFILTRAT |
| TC-U-CLEAN-01 | CLEANUP | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'CLEANUP' woul |
| TC-U-CLEAN-02 | CLEANUP | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'CLEANUP' woul |
| TC-U-CLEAN-03 | CLEANUP | OTHER | OTHER | FALLBACK | Gemini was attempted but failed (API unavailable). Fell back to rule result 'OTHER'. With working Gemini, 'CLEANUP' woul |

---

## Task 7 - Latency

> **Methodology**: Gemini client pre-warmed before timing begins.
> Rule latency = time for `rule_clf.classify()` only.
> Hybrid latency = time for `hybrid_clf.classify()` including Gemini if invoked.
> Gemini latency = estimated as `hybrid - rule` for invocation cases.

| Component | Avg (ms) | Min (ms) | Max (ms) |
| :--- | ---: | ---: | ---: |
| Rule Classifier | 0.187 | 0.0463 | 2.4085 |
| Hybrid Pipeline | 230.1812 | 189.8799 | 572.1721 |
| Gemini (estimated) | 229.9942 | 189.8336 | 569.7636 |

---

## Interpretation: Did the Hybrid Architecture Demonstrate Measurable Benefit?

> [!CAUTION]
> **Gemini was unavailable in this evaluation run.** The hybrid architecture
> CANNOT be evaluated for Gemini-added value in this run.

The evaluation demonstrates the **failure mode** of the hybrid system when the
Gemini API is unavailable: all novel/ambiguous commands that lack rule matches fall
through to `FALLBACK` with `intent=OTHER`, potentially misclassifying them.

**Implication for academic report**:
- The rule engine achieves high accuracy on commands within its signature vocabulary.
- For novel commands outside rule patterns, the system requires a working Gemini API
  to avoid defaulting to `OTHER`.
- The hybrid architecture's value proposition depends on Gemini availability.
- This is a valid architectural finding: the system degrades gracefully but loses
  classification capability for novel behaviours when Gemini is offline.

---

## Limitations

1. **28 cases** - too small for statistical significance.
2. **Gemini variability** - LLM responses are non-deterministic; re-running may yield different results.
3. **Synthetic events** - NormalizedEvent objects mirror Cowrie structure but are not raw JSON from a live session.
4. **Gemini API dependency** - If API key is missing or times out, all novel-command classifications fall to OTHER.
5. **Case design** - Cases were authored by the experimenter, introducing selection bias.
6. **No multi-event context** - Single-event evaluation does not test session-level context influence.

---

## Generated Files

| File | Description |
| :--- | :--- |
| `unseen_dataset.csv` | 28 labelled unseen cases |
| `unseen_results.csv` | Per-case results with rule, Gemini, hybrid outputs |
| `unseen_metrics.json` | All metrics, hybrid value analysis, error analysis |
| `confusion_matrix_rule.png` | Rule-only confusion matrix |
| `confusion_matrix_hybrid.png` | Hybrid confusion matrix |
| `latency_results.csv` | Latency breakdown |
| `unseen_evaluation_report.md` | This document |