# backend/services/severity_engine.py
import os
from dotenv import load_dotenv

load_dotenv()

FIRE_TEMP_WARNING  = float(os.getenv("FIRE_TEMP_WARNING",  60))
FIRE_TEMP_CRITICAL = float(os.getenv("FIRE_TEMP_CRITICAL", 150))
SMOKE_WARNING      = float(os.getenv("SMOKE_WARNING",      40))
SMOKE_CRITICAL     = float(os.getenv("SMOKE_CRITICAL",     70))
GAS_WARNING        = float(os.getenv("GAS_WARNING",        300))
GAS_CRITICAL       = float(os.getenv("GAS_CRITICAL",       600))


def compute_severity(
    confidence: float = 0.0,
    temperature: float = 0.0,
    smoke: float = 0.0,
    gas: float = 0.0,
) -> str:
    """Return LOW | MEDIUM | HIGH | CRITICAL based on combined inputs."""
    score = 0

    # Vision confidence (0-1)
    if confidence >= 0.80:
        score += 7  # Immediately triggers CRITICAL
    elif confidence >= 0.70:
        score += 4  # Immediately triggers HIGH
    elif confidence >= 0.60:
        score += 2  # Immediately triggers MEDIUM

    # Temperature
    if temperature >= FIRE_TEMP_CRITICAL:
        score += 3
    elif temperature >= FIRE_TEMP_WARNING:
        score += 1

    # Smoke %
    if smoke >= SMOKE_CRITICAL:
        score += 3
    elif smoke >= SMOKE_WARNING:
        score += 1

    # Gas ppm
    if gas >= GAS_CRITICAL:
        score += 3
    elif gas >= GAS_WARNING:
        score += 1

    if score >= 7:
        return "CRITICAL"
    elif score >= 4:
        return "HIGH"
    elif score >= 2:
        return "MEDIUM"
    else:
        return "LOW"


def get_response_recommendation(severity: str) -> str:
    mapping = {
        "LOW":      "Continue monitoring. No immediate action required.",
        "MEDIUM":   "Alert site supervisor. Inspect the area immediately.",
        "HIGH":     "Evacuate personnel. Notify fire department (dial 101).",
        "CRITICAL": "DISPATCH FIRE TRUCK IMMEDIATELY. Full evacuation. Activate sprinklers.",
    }
    return mapping.get(severity, "Monitor the situation.")
