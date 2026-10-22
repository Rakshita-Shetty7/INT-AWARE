"""
ML Model Registry & Provenance Management.

Tracks deployed model metadata, cryptographic hashes, performance baselines,
hyperparameter configurations, and feature pipeline schemas.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
REGISTRY_FILE = ARTIFACTS_DIR / "model_registry.json"


class ModelMetadata(BaseModel):
    """Provenance and specification metadata for a deployed machine learning model."""
    model_id: str = Field(..., description="Unique model identifier, e.g. intaware_svc_v1")
    version: str = Field(..., description="Semantic version string, e.g. 1.0.0")
    model_family: str = Field(..., description="Algorithm family, e.g. LinearSVC_Calibrated")
    artifact_path: str = Field(..., description="Path to serialized joblib bundle")
    artifact_sha256: str = Field(..., description="SHA-256 integrity hash of model artifact")
    dataset_version: str = Field("v1.0-primary", description="Corpus version used for training")
    dataset_sha256: Optional[str] = Field(None, description="SHA-256 hash of training data")
    trained_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    primary_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Held-out evaluation metrics: accuracy, macro_f1, brier_score, etc."
    )
    hyperparameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configured training hyperparameters"
    )
    feature_schema: List[str] = Field(
        default_factory=list,
        description="Feature extractors used in pipeline"
    )
    is_active: bool = Field(True, description="Whether this is the currently deployed primary model")


class ModelRegistry:
    """Manages model cataloging, provenance validation, and active deployment pointers."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or REGISTRY_FILE
        self._models: Dict[str, ModelMetadata] = {}
        self._load_registry()

    def _compute_sha256(self, file_path: Path) -> str:
        """Computes SHA-256 hash of a file."""
        if not file_path.exists():
            return "FILE_NOT_FOUND"
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _load_registry(self) -> None:
        """Loads registered models from JSON file or initializes default entry."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for m in data.get("models", []):
                        meta = ModelMetadata(**m)
                        self._models[meta.model_id] = meta
                return
            except Exception as e:
                logger.warning("Could not read registry from %s: %s", self.registry_path, e)

        # Initialize default registered baseline model
        artifact_path = ARTIFACTS_DIR / "intent_classifier.joblib"
        sha = self._compute_sha256(artifact_path)
        default_meta = ModelMetadata(
            model_id="intaware_linear_svc_calibrated_v1",
            version="1.0.0",
            model_family="CalibratedClassifierCV(LinearSVC)",
            artifact_path=str(artifact_path),
            artifact_sha256=sha,
            dataset_version="v1.0-primary",
            primary_metrics={
                "accuracy": 0.9449,
                "macro_f1": 0.9229,
                "weighted_f1": 0.9450,
            },
            hyperparameters={
                "C": 1.0,
                "calibration_cv": 3,
                "calibration_method": "sigmoid",
                "loss": "squared_hinge",
            },
            feature_schema=[
                "TfidfVectorizer(word, ngram=(1,2), sublinear_tf=True)",
                "TfidfVectorizer(char_wb, ngram=(3,6), sublinear_tf=True)",
            ],
            is_active=True,
        )
        self._models[default_meta.model_id] = default_meta
        self.save_registry()

    def save_registry(self) -> None:
        """Persists model catalog to JSON file."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "models": [m.model_dump(mode="json") for m in self._models.values()],
            }
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error("Failed to save model registry: %s", e)

    def register_model(self, metadata: ModelMetadata) -> None:
        """Registers a new model or updates an existing entry."""
        if metadata.is_active:
            for m in self._models.values():
                m.is_active = False
        self._models[metadata.model_id] = metadata
        self.save_registry()

    def get_active_model(self) -> Optional[ModelMetadata]:
        """Returns the currently designated active model."""
        for m in self._models.values():
            if m.is_active:
                return m
        return next(iter(self._models.values()), None)

    def verify_active_artifact_integrity(self) -> Tuple[bool, str]:
        """Verifies that the on-disk artifact matches the recorded SHA-256 hash."""
        active = self.get_active_model()
        if not active:
            return False, "No active model registered"
        current_sha = self._compute_sha256(Path(active.artifact_path))
        if current_sha == active.artifact_sha256:
            return True, f"Integrity verified (SHA-256: {current_sha[:16]}...)"
        return False, f"Hash mismatch: expected {active.artifact_sha256[:16]}..., found {current_sha[:16]}..."

    def verify_all_artifacts_integrity(self) -> Dict[str, Tuple[bool, str]]:
        """Verifies on-disk integrity for all cataloged models against their registered SHA-256."""
        results = {}
        for m_id, meta in self._models.items():
            current_sha = self._compute_sha256(Path(meta.artifact_path))
            if current_sha == meta.artifact_sha256:
                results[m_id] = (True, f"Integrity verified (SHA-256: {current_sha[:16]}...)")
            else:
                results[m_id] = (False, f"Hash mismatch: expected {meta.artifact_sha256[:16]}..., found {current_sha[:16]}...")
        return results

    def list_models(self) -> List[ModelMetadata]:
        """Returns list of all cataloged models."""
        return list(self._models.values())


# Global singleton
model_registry = ModelRegistry()
