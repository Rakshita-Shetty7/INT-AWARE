import React from 'react';
import { Link } from 'react-router-dom';
import {
  Award,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  ShieldCheck,
  Cpu,
  Layers,
  Terminal,
  Activity,
  ArrowRight,
  Info,
} from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const ModelPerformanceDocsPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-1">
          Empirical Validation & Testing
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Model Performance & Testing Methodology
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Verified evaluation metrics, per-class statistical results, cross-validation benchmarks, and automated software test results from the committed pipeline artifacts.
        </p>
      </div>

      <Callout type="info" title="Scientific Transparency Guarantee">
        All numbers presented on this page are extracted directly from committed evaluation artifacts (
        <code>backend/app/ml/artifacts/metrics.json</code>) and executed test runs. In strict accordance with our technical honesty policy, zero metrics, test counts, or benchmark outputs are fabricated or extrapolated.
      </Callout>

      {/* Distinction Section: ML Evaluation vs Software Testing */}
      <div className="p-5 rounded-2xl bg-[#090e1c] border border-cyan-800/50 space-y-3">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          Understanding the Distinction: Model Evaluation vs. Software Testing
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-300">
          <div className="p-3.5 rounded-xl bg-[#060913] border border-slate-800 space-y-1.5">
            <span className="font-bold text-cyan-400 block font-mono">1. Machine Learning Evaluation</span>
            <p className="text-slate-400 leading-relaxed">
              Assesses the statistical ability of the trained classification model to generalize attacker commands to correct intent categories. Evaluated via scikit-learn on strictly partitioned held-out datasets (standard holdout and leave-families-out).
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-[#060913] border border-slate-800 space-y-1.5">
            <span className="font-bold text-emerald-400 block font-mono">2. Software Unit & Integration Testing</span>
            <p className="text-slate-400 leading-relaxed">
              Verifies functional correctness and fault tolerance of software code: API route validation, log tailing, race condition handling, risk score calculation, session state machines, and MongoDB aggregations.
            </p>
          </div>
        </div>
      </div>

      {/* Model Architecture & Specification */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          1. Machine Learning Model Architecture
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Model Name</span>
            <span className="text-slate-200 font-bold">Calibrated LinearSVC</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Calibration Method</span>
            <span className="text-cyan-400 font-bold">Sigmoidal Platt Scaling</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Feature Representation</span>
            <span className="text-indigo-400 font-bold">TF-IDF Char (2-5) & Word (1-3)</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Vocabulary Dimension</span>
            <span className="text-slate-200 font-bold">Up to 40,000 n-grams</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Confidence Metric</span>
            <span className="text-purple-400 font-bold">Shannon Prediction Entropy</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-slate-500 block text-[10px] uppercase">Out-of-Distribution</span>
            <span className="text-amber-400 font-bold">Vocabulary Novelty Scoring</span>
          </div>
        </div>
      </div>

      {/* Dataset & Cross-Validation */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          2. Dataset & Model Selection Cross-Validation
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          The dataset contains <strong>6,867 unique command samples</strong> across <strong>243 template families</strong>. Ten exact duplicate strings were filtered out to eliminate shortcut learning. Model candidates were benchmarked using 4-fold Stratified K-Fold cross-validation on the training set:
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="p-2.5">Candidate Model</th>
                <th className="p-2.5">CV Macro F1 (Mean ± Std)</th>
                <th className="p-2.5">Decision</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-800/60 bg-cyan-950/20 text-cyan-300">
                <td className="p-2.5 font-bold">LinearSVC (Calibrated with Sigmoid)</td>
                <td className="p-2.5 font-bold">0.9990 ± 0.0007</td>
                <td className="p-2.5 text-emerald-400 font-bold">Selected Model</td>
              </tr>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5">Logistic Regression (L2, C=1.0)</td>
                <td className="p-2.5">0.9973 ± 0.0015</td>
                <td className="p-2.5 text-slate-500">Benchmark Baseline</td>
              </tr>
              <tr className="border-b border-slate-800/60 text-slate-300">
                <td className="p-2.5">Complement Naive Bayes (alpha=0.1)</td>
                <td className="p-2.5">0.9859 ± 0.0059</td>
                <td className="p-2.5 text-slate-500">Fast Baseline</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Primary Evaluation Metrics Table */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          3. Primary Evaluation Results (Held-Out Test Split)
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          Evaluated on standard stratified 80/20 test split (5,493 train samples, 1,374 test samples). Leakage control is asserted: zero identical command strings appear in both train and test partitions.
        </p>

        {/* Global summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-cyan-800/50">
            <span className="text-2xl font-bold font-mono text-cyan-400">100.0%</span>
            <span className="block text-[11px] text-slate-400 uppercase font-semibold mt-0.5">Test Accuracy</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-indigo-800/50">
            <span className="text-2xl font-bold font-mono text-indigo-400">1.0000</span>
            <span className="block text-[11px] text-slate-400 uppercase font-semibold mt-0.5">Macro Precision</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-purple-800/50">
            <span className="text-2xl font-bold font-mono text-purple-400">1.0000</span>
            <span className="block text-[11px] text-slate-400 uppercase font-semibold mt-0.5">Macro Recall</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-emerald-800/50">
            <span className="text-2xl font-bold font-mono text-emerald-400">1.0000</span>
            <span className="block text-[11px] text-slate-400 uppercase font-semibold mt-0.5">Macro F1 Score</span>
          </div>
        </div>

        {/* Per-class metrics table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="p-2.5">Intent Category</th>
                <th className="p-2.5">Test Support</th>
                <th className="p-2.5">Precision</th>
                <th className="p-2.5">Recall</th>
                <th className="p-2.5">F1-Score</th>
              </tr>
            </thead>
            <tbody>
              {[
                { name: 'RECONNAISSANCE', support: 139, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'DISCOVERY', support: 194, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'CREDENTIAL_ACCESS', support: 144, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'EXECUTION', support: 164, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'PRIVILEGE_ESCALATION', support: 120, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'PERSISTENCE', support: 115, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'EXPLOITATION', support: 105, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'EXFILTRATION', support: 126, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'CLEANUP', support: 99, p: '1.00', r: '1.00', f1: '1.00' },
                { name: 'OTHER', support: 168, p: '1.00', r: '1.00', f1: '1.00' },
              ].map((row) => (
                <tr key={row.name} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                  <td className="p-2.5 text-cyan-400 font-bold">{row.name}</td>
                  <td className="p-2.5 text-slate-300">{row.support} samples</td>
                  <td className="p-2.5 text-emerald-400">{row.p}</td>
                  <td className="p-2.5 text-emerald-400">{row.r}</td>
                  <td className="p-2.5 text-emerald-400 font-bold">{row.f1}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Robustness Evaluation (Leave-Families-Out) */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          4. Robustness Evaluation: Leave-Families-Out Holdout
        </h2>
        <div className="p-4 rounded-xl bg-[#090e1c] border border-cyan-800/50 space-y-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-cyan-400 text-sm">Out-of-Distribution Generalization Benchmark</span>
            <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 font-mono text-[10px] border border-cyan-800">
              Zero Template Leakage · 50 Families Held Out
            </span>
          </div>
          <p className="text-slate-300 leading-relaxed">
            In standard NLP, models can memorize syntactic motifs if commands from the same template family appear in both train and test splits. To evaluate true zero-shot generalization to unseen command syntaxes, we partition the dataset by entire template families (5,430 train samples, 1,437 held-out test samples across 50 distinct template families):
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1 text-center font-mono">
            <div className="p-3 bg-[#060913] rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] block">ROBUSTNESS ACCURACY</span>
              <span className="text-xl font-bold text-cyan-400">81.98%</span>
              <span className="text-[10px] text-slate-500 block">Baseline: 54.63%</span>
            </div>
            <div className="p-3 bg-[#060913] rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] block">ROBUSTNESS MACRO-F1</span>
              <span className="text-xl font-bold text-cyan-400">0.8153</span>
              <span className="text-[10px] text-slate-500 block">Baseline: 0.5038</span>
            </div>
            <div className="p-3 bg-[#060913] rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] block">WEIGHTED F1 SCORE</span>
              <span className="text-xl font-bold text-indigo-400">0.8146</span>
              <span className="text-[10px] text-slate-500 block">Support: 1,437</span>
            </div>
            <div className="p-3 bg-[#060913] rounded-lg border border-slate-800">
              <span className="text-slate-400 text-[10px] block">INFERENCE LATENCY</span>
              <span className="text-xl font-bold text-emerald-400">11.83 ms</span>
              <span className="text-[10px] text-slate-500 block">P95: 20.36 ms</span>
            </div>
          </div>

          <h3 className="text-xs font-bold text-white uppercase tracking-wider pt-2">Leave-Families-Out Per-Class Breakdown</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400">
                  <th className="p-2">Intent Category</th>
                  <th className="p-2">Test Support</th>
                  <th className="p-2">Precision</th>
                  <th className="p-2">Recall</th>
                  <th className="p-2">F1-Score</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { name: 'CLEANUP', support: 96, p: '0.9333', r: '0.8750', f1: '0.9032' },
                  { name: 'CREDENTIAL_ACCESS', support: 153, p: '1.0000', r: '0.7320', f1: '0.8453' },
                  { name: 'DISCOVERY', support: 201, p: '0.6089', r: '0.6816', f1: '0.6432' },
                  { name: 'EXECUTION', support: 175, p: '1.0000', r: '0.9714', f1: '0.9855' },
                  { name: 'EXFILTRATION', support: 140, p: '1.0000', r: '0.9786', f1: '0.9892' },
                  { name: 'EXPLOITATION', support: 140, p: '0.6667', r: '1.0000', f1: '0.8000' },
                  { name: 'OTHER', support: 175, p: '0.7917', r: '0.6514', f1: '0.7147' },
                  { name: 'PERSISTENCE', support: 118, p: '0.8194', r: '1.0000', f1: '0.9008' },
                  { name: 'PRIVILEGE_ESCALATION', support: 96, p: '1.0000', r: '0.3646', f1: '0.5344' },
                  { name: 'RECONNAISSANCE', support: 143, p: '0.7706', r: '0.9161', f1: '0.8371' },
                ].map((row) => (
                  <tr key={row.name} className="border-b border-slate-800/40 text-slate-300">
                    <td className="p-2 font-bold text-white">{row.name}</td>
                    <td className="p-2">{row.support}</td>
                    <td className="p-2 text-cyan-400">{row.p}</td>
                    <td className="p-2 text-cyan-400">{row.r}</td>
                    <td className="p-2 text-cyan-400 font-bold">{row.f1}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="text-slate-400 text-[11px] pt-1 leading-relaxed">
            <em>Operational interpretation:</em> The integration of canonicalization and domain semantic features lifted unseen family generalization from 54.63% to 81.98%. For remaining ambiguities (such as privilege escalation via kernel exploit compilation vs initial exploitation), the runtime hybrid arbiter consults deterministic rule signatures and optional Gemini reasoning.
          </p>
        </div>
      </div>

      {/* Software Test Suite Verification */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white border-b border-slate-800 pb-2">
          5. Automated Software Test Suite Execution
        </h2>
        <p className="text-xs text-slate-300 leading-relaxed">
          The software backend is tested via an extensive, hermetic pytest suite. Tests run against in-memory MongoDB mocks (<code>mongomock</code>) and Starlette <code>TestClient</code>, requiring zero live databases or internet connectivity:
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono">
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-2xl font-bold text-white">166</span>
            <span className="block text-[11px] text-slate-400 uppercase mt-0.5">Tests Discovered</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-emerald-800/50">
            <span className="text-2xl font-bold text-emerald-400">166</span>
            <span className="block text-[11px] text-slate-400 uppercase mt-0.5">Tests Passed (100%)</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-2xl font-bold text-slate-400">0</span>
            <span className="block text-[11px] text-slate-400 uppercase mt-0.5">Tests Failed</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090e1c] border border-slate-800">
            <span className="text-2xl font-bold text-slate-400">0</span>
            <span className="block text-[11px] text-slate-400 uppercase mt-0.5">Tests Skipped</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#090e1c] border border-slate-800 text-xs text-slate-300 space-y-2">
          <div className="font-bold text-white flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            Verification Execution Command
          </div>
          <CodeBlock
            code={`.venv/Scripts/pytest -v
# Output: 166 passed, 1 warning in 90.08s`}
            language="bash"
            title="Hermetic Test Execution"
          />
          <div className="flex items-center justify-between text-slate-400 text-[11px] pt-1">
            <span>Test Coverage Status:</span>
            <span className="font-mono text-amber-400 font-semibold">Not measured (coverage tool not enforced in CI)</span>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/architecture" className="text-slate-400 hover:text-white">
          ← Architecture & Pipeline
        </Link>
        <Link to="/docs/api" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>REST & WebSocket API Reference</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};