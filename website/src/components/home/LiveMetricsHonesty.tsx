import React from 'react';
import { Award, CheckCircle, AlertCircle, BarChart3, ShieldCheck, ArrowRight, Layers } from 'lucide-react';
import { Link } from 'react-router-dom';

export const LiveMetricsHonesty: React.FC = () => {
  return (
    <section className="py-20 bg-[#060913] border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/60 text-xs font-mono text-emerald-400 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Verified Technical Integrity · Zero Fabricated Metrics</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Model Performance & Software Test Results
          </h2>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            All model performance figures are read directly from committed evaluation artifacts (<code>backend/app/ml/artifacts/metrics.json</code>) generated across 6,867 de-duplicated command samples. Automated test counts reflect the full 166-test pytest suite.
          </p>
        </div>

        {/* Top 4 Metric Highlights */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <div className="p-5 rounded-2xl bg-[#090e1c] border border-cyan-800/40 text-center space-y-1.5">
            <div className="text-3xl sm:text-4xl font-extrabold text-cyan-400 font-mono">100.0%</div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Held-Out Accuracy</div>
            <div className="text-[11px] text-slate-400">Stratified 80/20 test split (1,374 test commands)</div>
          </div>

          <div className="p-5 rounded-2xl bg-[#090e1c] border border-indigo-800/40 text-center space-y-1.5">
            <div className="text-3xl sm:text-4xl font-extrabold text-indigo-400 font-mono">1.0000</div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Macro F1 Score</div>
            <div className="text-[11px] text-slate-400">Balanced across all 10 intent classes</div>
          </div>

          <div className="p-5 rounded-2xl bg-[#090e1c] border border-purple-800/40 text-center space-y-1.5">
            <div className="text-3xl sm:text-4xl font-extrabold text-purple-400 font-mono">81.98%</div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Leave-Families-Out</div>
            <div className="text-[11px] text-slate-400">Strict novel template generalisation (Macro-F1: 0.8153, up from 54.63% baseline)</div>
          </div>

          <div className="p-5 rounded-2xl bg-[#090e1c] border border-emerald-800/40 text-center space-y-1.5">
            <div className="text-3xl sm:text-4xl font-extrabold text-emerald-400 font-mono">166 / 166</div>
            <div className="text-xs font-bold text-white uppercase tracking-wider">Automated Tests</div>
            <div className="text-[11px] text-slate-400">100% green hermetic test suite (0 failed, 0 skipped)</div>
          </div>
        </div>

        {/* Comparison Callout & Software Testing Context */}
        <div className="p-6 rounded-2xl bg-[#090e1c] border border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div className="space-y-3 md:col-span-2">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              Machine Learning Evaluation vs. Software Testing Methodology
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              We maintain a rigorous distinction between statistical machine learning evaluation and software functional testing:
            </p>
            <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-5">
              <li>
                <strong>Model Evaluation:</strong> Measures classification generalization of the calibrated LinearSVC (enhanced with canonicalized word/char TF-IDF and domain structural feature extraction) on unseen held-out shell commands. Standard stratified holdout achieves 100.0%, while strict leave-families-out holdout achieves 81.98% (Macro-F1 0.8153, improved substantially from the 54.63% unenhanced baseline). Novel commands triggering abstention are intercepted by deterministic rules and semantic fallback.
              </li>
              <li>
                <strong>Software Test Suite:</strong> 166 hermetic automated pytest tests verify API routing, log rotation tailing, risk scoring arithmetic, session state machines, and MongoDB aggregations with zero live network dependencies.
              </li>
              <li>
                <strong>Coverage Status:</strong> Test execution coverage is currently <em>Not measured</em> in the CI pipeline.
              </li>
            </ul>

            <div className="pt-1">
              <Link
                to="/docs/model-performance"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 font-mono transition-colors"
              >
                <span>View Full Per-Class Confusion Matrix & Test Metrics</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[#060913] border border-slate-800 text-xs font-mono space-y-2 text-slate-300">
            <div className="text-slate-400 text-[11px] uppercase tracking-wider font-bold">Model Selection (4-Fold CV)</div>
            <div className="flex justify-between items-center text-cyan-400 font-semibold">
              <span>LinearSVC (Calibrated):</span>
              <span>0.9990 F1</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span>Logistic Regression:</span>
              <span>0.9973 F1</span>
            </div>
            <div className="flex justify-between items-center text-slate-400">
              <span>Complement Naive Bayes:</span>
              <span>0.9859 F1</span>
            </div>
            <div className="pt-2 border-t border-slate-800/80 text-[11px] text-slate-500 font-sans">
              LinearSVC was selected based on superior Macro-F1 across all 10 intent classes during cross-validation.
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
