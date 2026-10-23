"""Scoped compatibility shim for the HA-VLN Blackwell launcher."""
import numpy as np

# Habitat-Sim 0.1.7 still references np.float in a few Python helpers.
# Keep the alias local to processes launched with scripts/blackwell_compat on PYTHONPATH.
if not hasattr(np, "float"):
    np.float = float
