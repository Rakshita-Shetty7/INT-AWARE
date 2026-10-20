# INTENT-AWARE DECEPTION SYSTEM FOR REAL-TIME ATTACKER PROFILING
## Scientific Literature Review, Prior Art Analysis, and Research Novelty Specification

---

### Abstract & Research Vision

Modern intrusion detection systems (IDS) and honeypots typically operate in two disparate regimes: passive static observation (e.g., standard Cowrie, Dionaea honeypots) or reactive signature-based blocking (e.g., Snort, Suricata). While static honeypots collect raw command telemetry, they suffer from rapid fingerprinting by automated scanning tools and provide static, predictable responses. Conversely, machine learning approaches for command classification often evaluate commands in isolation, ignoring temporal progression, exhibiting overconfidence on out-of-distribution (OOD) payloads, and lacking safe closed-loop adaptive deception capabilities.

The **INTENT-AWARE DECEPTION SYSTEM FOR REAL-TIME ATTACKER PROFILING** (INT-AWARE) addresses these challenges through a unified, evidence-driven cyber deception framework. INT-AWARE formulates attacker-defender interaction as a real-time, state-aware cyber deception game where defender deception policies are dynamically adjusted according to inferred attacker intent, skill level, and temporal progression across MITRE ATT&CK stages.

---

### 1. Comprehensive Literature Review & Prior Art Taxonomy

To establish our research novelty, we examine existing peer-reviewed literature across five foundational axes:

| Research Domain | Key Prior Works | State-of-the-Art Limitations | INT-AWARE Proposed Advance |
| :--- | :--- | :--- | :--- |
| **Command-Level Intent Classification** | Al-Ibrahim et al. (2020), MITRE ATT&CK evaluations, Tian et al. (2021) | Evaluates commands in isolation; high vulnerability to out-of-distribution (OOD) commands; zero abstention capability. | Calibrated Hybrid Classifier (LinearSVC + Word/Char N-Grams + Deterministic Rules + LLM Fallback) with epistemic uncertainty estimation and OOD novelty detection. |
| **Attack-Stage & Sequence Modeling** | Sendi et al. (2012), Holgado et al. (2020), Hidden Markov Models for APT stage tracking | Rigid multistep attack graphs; inability to handle interleaved, multi-threaded, or out-of-order commands; high state space explosion. | Empirical Attacker Transition Graph $P(\text{Intent}_{t+1} \mid \text{Intent}_t, \text{Stage}_t)$ with dynamic transition anomaly scoring and online Bayesian stage updating. |
| **Honeypot Deception & Tar-pitting** | Spitzner (2003), Provos (Honeyd, 2004), Dowling et al. (2020 Cowrie advancements) | Static file system responses; trivially fingerprinted by TTL, banner matching, and identical error strings; zero adaptation to attacker intent. | Adaptive Closed-Loop Deception Engine with Intent-Conditioned Decoy Injection (honeytokens, synthetic configs, delay tar-pitting, synthetic credential traps) with strict zero-host execution safety. |
| **Attacker Profiling & Attribution** | Pei et al. (2019), Bilge et al. (2017), Cichonski et al. (NIST SP 800-61) | Relies primarily on brittle network attributes (IP, ASN) or requires massive offline graph clustering over months of historical data. | Real-time multi-signal behavioral profiling (TTP entropy, command vocabulary Jaccard similarity, temporal pacing, credential reuse vectors). |
| **Industrial / Cyber-Physical AI Security** | Goh et al. (SWaT dataset, 2016), Ahmed et al. (WADI dataset, 2017), Shin et al. (HAI dataset, 2020–2022) | Benchmark models evaluated on synthetic stationary assumptions; vulnerable to sensor spoofing and adversarial perturbation. | Industrial Robustness & Adversarial Testing Module evaluating temporal sensor invariants and adversarial perturbation bounds. |

---

### 2. Limitations of Existing Commercial & Open-Source Solutions

1. **Standard Cowrie Honeypot**:
   - Offers static command responses stored in text templates.
   - Attackers executing `uname -a`, `cat /proc/cpuinfo`, or `wget` encounter uniform responses that alert sophisticated adversaries within 3 commands.
   - Fails to generate dynamic canary tokens or monitor how injected deception tokens travel across subsequent commands.

2. **Traditional ML Classifiers (TF-IDF / Naive Bayes / Random Forest)**:
   - Forced Choice Fallacy: Every input is assigned to one of $K$ classes with $\sum p_i = 1.0$, even when presented with random noise, base64 blobs, or novel zero-day commands.
   - Lack calibrated probabilities: Reported 99% confidence scores frequently represent uncalibrated softmax logits rather than empirical posterior probabilities.

3. **Rule-Only Engines (e.g. Sigma, Snort)**:
   - High precision on known strings (`cat /etc/shadow`), but zero generalizability to syntactic variations, variable aliasing, or novel malware staging commands (`curl -fsSL https://... | sh`).

---

### 3. Formal Research Questions (RQ)

- **RQ1 (Intent Generalizability & Abstention)**: Can a calibrated hybrid intent classification pipeline maintain $\ge 90\%$ macro-F1 on known distributions while reliably abstaining (entropy thresholding $\mathcal{H}(P) \ge \tau_{\text{abstain}}$) on OOD commands without false overconfidence?
- **RQ2 (Temporal Transition Predictive Power)**: Does modeling attacker command sequences as an empirical Markov transition graph significantly improve next-intent prediction compared to zero-order static baselines?
- **RQ3 (Adaptive Engagement Dwell-Time)**: Does intent-conditioned adaptive deception (delay tar-pitting, synthetic honeytoken generation) statistically extend attacker session duration (dwell time) and command engagement depth without violating isolation constraints?
- **RQ4 (Multi-Signal Behavioral Profiling)**: To what degree can multi-signal behavioral fingerprinting (command n-gram vocabulary, inter-command timing distributions, MITRE technique vectors) cluster related sessions across distinct IP subnets?

---

### 4. Technical Novelty & Proposed Architectural Contributions

```
+---------------------------------------------------------------------------------------------------+
|                        INT-AWARE HYBRID & ADAPTIVE ARCHITECTURE                                   |
+---------------------------------------------------------------------------------------------------+
                                             |
                                  Telemetry Event Ingestion
                                             |
                   +-------------------------+-------------------------+
                   |                                                   |
       [Command-Level Pipeline]                              [Session-Level Pipeline]
                   |                                                   |
         Normalized Input Command                            Sequence Window [C_1, ..., C_t]
                   |                                                   |
       +-----------+-----------+                                       |
       |                       |                                       |
  Rule Classifier      ML Classifier (TF-IDF + Calibrated SVC)         |
  (High Precision)     + OOD Novelty Estimator (Isolation/Entropy)      |
       |                       |                                       |
       +-----------+-----------+                                       |
                   |                                                   |
           Arbitration Engine                                          |
       (Deterministic > High-Conf ML                                   |
        > OOD Abstention > LLM Fallback)                               |
                   |                                                   |
        Calibrated Intent Output                                       |
                   |                                                   |
                   +-------------------> [Temporal Transition Model] <--+
                                                   |
                                       Markov State / Stage Tracker
                                       - Next-Intent Probability Distribution
                                       - Sequence Anomaly Scoring
                                                   |
                                       [Evidence-Backed Risk Engine]
                                       - Explainable Linear Additive Scoring
                                       - Factor Breakdown with Provenance
                                                   |
                                       [Adaptive Deception Engine]
                                       - Zero-Host Safety Gatekeeper
                                       - Dynamic Response Selector (Decoy, Tar-pit, Canary)
                                       - Engagement & Dwell-Time Analytics
                                                   |
                                       [Real-Time State Persistence & WS]
                                       - MongoDB Document Provenance
                                       - React Multi-View Investigation Dashboard
```

#### Contribution 1: Epistemic Uncertainty Estimation & Out-of-Distribution Novelty Detector
We implement a dual-gate novelty detector combining character-level reconstruction perplexity, TF-IDF out-of-vocabulary ratio, and prediction entropy:
$$\mathcal{H}(\hat{\mathbf{p}}) = - \sum_{k=1}^{10} \hat{p}_k \log_2(\hat{p}_k)$$
When $\mathcal{H}(\hat{\mathbf{p}}) > \tau_{\text{entropy}}$ or token novelty $> \tau_{\text{novelty}}$, the classifier tags the command as `NOVEL_UNSEEN` and activates the bounded LLM fallback with verified structured schema output, preventing silent misclassification.

#### Contribution 2: Empirical Markov Sequence & Attack Stage Transition Engine
Rather than treating session commands as independent identically distributed (i.i.d.) events, we maintain a transition matrix $T_{i, j} = P(\text{Intent}_{t} = j \mid \text{Intent}_{t-1} = i)$ computed across validated attack campaigns. This yields:
1. Online forward projection of the adversary's next likely intent.
2. Sequence anomaly detection: Jumps with $T_{i,j} < \epsilon_{\text{threshold}}$ trigger anomaly alerts.

#### Contribution 3: Hardened, Intent-Conditioned Adaptive Deception Engine
A dedicated module generates synthetic responses mapped to attacker intent:
- **Reconnaissance**: Returns plausible, deceptive host architecture metadata, decoy open ports, and synthetic kernel versions.
- **Discovery**: Returns synthetic directories and simulated user listings containing honeytokens (canary API keys, dummy database connection strings).
- **Credential Access**: Emits realistic bcrypt/shadow hashes containing honeytokens that alert defender infrastructure if cracked and queried elsewhere.
- **Execution / Exploitation**: Activates intelligent tar-pitting (proportional response latency scaling up to 1500ms) to exhaust automated scanner threads while logging payloads.
- **Safety Guarantee**: Strictly deterministic, sandboxed emulation; **Zero raw shell execution on the host system**.

---

### 5. Verification & Experimental Plan

1. **Phase B Implementation**: Implement Novelty Detection, Sequence Transition Model, and Adaptive Deception Engine in `backend/app/services/`.
2. **Unit & Integration Suite**: Verify each engine component with 100% deterministic test coverage.
3. **Ablation Studies**: Measure accuracy, calibration curves (Brier score, ECE), and false positive rates with/without novelty abstention.
4. **Empirical Benchmarks**: Evaluate dwell time and command engagement metrics under adaptive deception versus static Cowrie responses.
