import React from 'react';
import { Link } from 'react-router-dom';
import { GitPullRequest, CheckCircle2, ShieldCheck, Terminal, ArrowRight } from 'lucide-react';
import { CodeBlock } from '../../components/docs/CodeBlock';
import { Callout } from '../../components/docs/Callout';

export const ContributingPage: React.FC = () => {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-1">
          Developer Guidelines
        </div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Contributing & Developer Verification Guide
        </h1>
        <p className="text-slate-400 text-sm leading-relaxed mt-2">
          Standards for developing, testing, retraining ML classifiers, and code verification.
        </p>
      </div>

      <div className="space-y-6">
        {/* Section 1: Developer Environment */}
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            1. Local Developer Setup
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            Configure all dependencies in a Python 3.12+ virtual environment:
          </p>
          <CodeBlock
            code={`# Navigate to project root:
cd intent-aware-deception

# Create and activate virtual environment:
python -m venv .venv
# On Windows: .venv\\Scripts\\Activate.ps1
# On Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt`}
            language="bash"
            title="Developer Setup"
          />
        </div>

        {/* Section 2: Automated Test Suite */}
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2 flex items-center justify-between">
            <span>2. Running the Automated Test Suite (166 Tests)</span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
              166 / 166 Passed
            </span>
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            The platform maintains strict hermetic regression testing covering classifiers, model integrity, digital twin reconstruction, counterfactual simulations, and FastAPI endpoints:
          </p>
          <CodeBlock
            code={`# Run complete test suite:
pytest -v

# Run standout feature tests:
pytest tests/test_standout_features.py -v

# Run with test coverage:
pytest --cov=backend/app tests/`}
            language="bash"
            title="Execute Pytest"
          />
        </div>

        {/* Section 3: Retraining the ML Pipeline */}
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            3. Retraining the ML Classifier & Registry Integrity
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            To retrain the LinearSVC intent model on updated datasets:
          </p>
          <CodeBlock
            code="python -m backend.app.ml.train"
            language="bash"
            title="Train Model"
          />
          <Callout type="tip" title="SHA-256 Model Registry Guard">
            The training pipeline automatically computes the SHA-256 checksum of the trained <code>.joblib</code> artifact and updates <code>backend/app/ml/model_registry.json</code>. The FastAPI application verifies this cryptographic hash on startup to prevent model corruption or unauthorized tampering.
          </Callout>
        </div>

        {/* Section 4: Frontend Development */}
        <div>
          <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-2">
            4. Frontend Dashboard Development
          </h2>
          <p className="text-xs text-slate-300 leading-relaxed mt-2">
            The SOC command center uses React 19 and Vite:
          </p>
          <CodeBlock
            code={`cd frontend
npm install
npm run dev

# Verify production build:
npm run build`}
            language="bash"
            title="Frontend Workflow"
          />
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/maintenance" className="text-slate-400 hover:text-white">
          ← Stopping & Maintenance
        </Link>
        <Link to="/docs" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">
          <span>Return to Documentation Overview</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
