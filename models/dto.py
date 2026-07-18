# ponytail: shim — root models.dto re-exports from common/models/dto.py
# Prevents the dual-DTO pollution where legacy tests insert repo root first
# and shadow the canonical common DTO module.
# Loads the common file by ABSOLUTE PATH (never by import name to avoid
# recursion), then re-exports all its public symbols.

import os, importlib.util, sys

_COMMON_DTO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "functions", "suraksha_ai", "common", "models", "dto.py"
)

if os.path.exists(_COMMON_DTO):
    # Insert common/ on sys.path so the common dto's internal `from ... import`
    # statements resolve consistently. Last-position to avoid overriding any
    # caller-supplied path ordering; common tests insert at position 0.
    _common_dir = os.path.dirname(os.path.dirname(_COMMON_DTO))
    if _common_dir not in sys.path:
        sys.path.append(_common_dir)

    _spec = importlib.util.spec_from_file_location(
        "models.dto_common_canonical", _COMMON_DTO)
    _mod = importlib.util.module_from_spec(_spec)
    try:
        _spec.loader.exec_module(_mod)
    except Exception:
        # If the common module pulls in optional deps unavailable here,
        # fall back to the legacy replica instead of crashing all tests.
        _fallback = os.path.join(os.path.dirname(__file__), "dto_legacy.bak.py")
        if os.path.exists(_fallback):
            _spec = importlib.util.spec_from_file_location(
                "models.dto_legacy", _fallback)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
        else:
            raise

    for _name in dir(_mod):
        if not _name.startswith("_"):
            globals()[_name] = getattr(_mod, _name)
else:
    # Last resort: load legacy replica parked next to this file.
    _legacy = os.path.join(os.path.dirname(__file__), "dto_legacy.bak.py")
    if os.path.exists(_legacy):
        _spec = importlib.util.spec_from_file_location(
            "models.dto_legacy", _legacy)
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        for _name in dir(_mod):
            if not _name.startswith("_"):
                globals()[_name] = getattr(_mod, _name)
    else:
        raise ImportError("Neither common/models/dto.py nor legacy replica found")
