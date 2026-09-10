#!/usr/bin/env python3
"""
CLI Launcher for Cowrie Log Collector & Feature Extraction Engine.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.log_collector import cli_main

if __name__ == "__main__":
    cli_main()
