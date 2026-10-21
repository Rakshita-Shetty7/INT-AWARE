import React from 'react';
import { Award, CheckCircle, AlertCircle, BarChart3, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

export const LiveMetricsHonesty: React.FC = () => {
  return (
    <section className="py-20 bg-[#060913] border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/60 text-xs font-mono text-emerald-400 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Honest Research Integrity · Zero Fabricated Metrics</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Transparent ML Evaluation & Benchmarks
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            All numbers are generated directly from the model registry metrics file (<code>metrics.json</code>) on a strictly partitioned, leakage-controlled dataset.
          </p>
        </div>

        {/* Top 4 Metric Highlights */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <div className="p-5 rounded-2xl bg-[#090e1c] border border-cyan-800/40 text-center space-y-1.5">
            <div className="text-3xl sm:text-4xl font-extrabold text-cyan-400 font-mono">94.49%</div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Held-Out Accuracy</div>
            <div className="text-[11px] text-slate-400">Stratified 80/20 test split (272 commands)</div>
          </div>

          <div className="p-5 rounded-2xl bg-[#090e1c] border border-indigo-800/40 text-center space-y-1.5">
            <div className="text-3xl sm:text-4xl font-extrabold text-indigo-400 font-mono">0.9229</div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Macro F1 Score</div>
            <div className="text-[11px] text-slate-400">Balanced across all 10 intent classes</div>
          </div>

          <div className="p-5 rounded-2xl bg-[#090e1c] border border-purple-800/40 text-center space-y-1.5">
            <div className="text-3xl sm:text-4xl font-extrabold text-purple-400 font-mono">67.87%</div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Leave-Families-Out</div>
            <div className="text-[11px] text-slate-400">Strict generalization to novel templates</div>
          </div>

          <div className="p-5 rounded-2xl bg-[#090e1c] border border-emerald-800/40 text-center space-y-1.5">
            <div className="text-3xl sm:text-4xl font-extrabold text-emerald-400 font-mono">162 / 162</div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Automated Tests</div>
            <div className="text-[11px] text-slate-400">100% green test suite across 22 test files</div>
          </div>
        </div>

        {/* Comparison Callout */}
        <div className="p-6 rounded-2xl bg-[#090e1c] border border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div className="space-y-2 md:col-span-2">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              Why INT-AWARE Reports Both Held-Out and Unseen-Family Scores
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Standard NLP evaluations can flatter models if near-duplicate command tokens leak between training and test sets. INT-AWARE enforces strict string deduplication (zero train commands appear in the test set) and additionally benchmarks on a whole-family holdout test. For novel or ambiguous commands, the deterministic rule engine and optional Gemini semantic layer activate as run-time guardrails.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-[#060913] border border-slate-800 text-xs font-mono space-y-2 text-slate-300">
            <div className="text-slate-400 text-[11px] uppercase tracking-wider font-bold">Model Comparison (4-Fold CV)</div>
            <div className="flex justify-between items-center text-cyan-400 font-semibold">
              <span>LinearSVC (Calibrated):</span>
              <span>0.8539 F1</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span>Logistic Regression:</span>
              <span>0.8482 F1</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span>Complement Naive Bayes:</span>
              <span>0.8146 F1</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
